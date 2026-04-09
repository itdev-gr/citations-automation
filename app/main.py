import asyncio
import json
import csv
import io
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from contextlib import asynccontextmanager

from .database import (
    init_db, get_all_businesses, get_business, create_business,
    update_business, delete_business, get_submissions, get_all_submissions,
    upsert_submission, DIRECTORIES,
)
from .models import BusinessCreate, BusinessUpdate, SubmissionRequest, HumanActionComplete
from .automations.xo_gr import XoGrAutomation
from .automations.vrisko import VriskoAutomation
from .automations.europages import EuropagesAutomation
from .automations.bing_places import BingPlacesAutomation
from .automations.foursquare import FoursquareAutomation
from .automations.apple_business import AppleBusinessAutomation
from .automations.cybo import CyboAutomation
from .automations.infobel import InfobelAutomation

AUTOMATION_MAP = {
    "xo_gr": XoGrAutomation,
    "vrisko": VriskoAutomation,
    "europages": EuropagesAutomation,
    "bing_places": BingPlacesAutomation,
    "foursquare": FoursquareAutomation,
    "apple_business": AppleBusinessAutomation,
    "cybo": CyboAutomation,
    "infobel": InfobelAutomation,
}

# Global state for active automation
active_automation = None
sse_queues: list[asyncio.Queue] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Citations Automation Tool", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Business CRUD ---

@app.get("/api/businesses")
async def list_businesses():
    return await get_all_businesses()


@app.post("/api/businesses")
async def create_business_route(data: BusinessCreate):
    business_id = await create_business(data.model_dump())
    return {"id": business_id, "message": "Business created"}


# --- CSV Import/Export (before {business_id} routes) ---

@app.post("/api/businesses/import-csv")
async def import_csv(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    field_map = {
        "business_name": "name", "company_name": "name", "eponymia": "name",
        "name_en": "name_en", "english_name": "name_en",
        "address": "address", "dieuthinsi": "address", "street": "address",
        "city": "city", "poli": "city",
        "city_en": "city_en",
        "postal_code": "postal_code", "zip": "postal_code", "tk": "postal_code",
        "region": "region", "nomos": "region",
        "phone": "phone", "tilefono": "phone", "tel": "phone",
        "mobile": "mobile", "kinito": "mobile",
        "email": "email",
        "website": "website", "url": "website",
        "category": "category", "kategoria": "category",
        "category_en": "category_en",
        "description_gr": "description_gr", "perigrafi": "description_gr",
        "description_en": "description_en",
        "hours": "hours", "ores": "hours",
        "facebook": "facebook", "instagram": "instagram", "linkedin": "linkedin",
        "tax_id": "tax_id", "afm": "tax_id",
        "contact_person": "contact_person",
    }

    imported = 0
    for row in reader:
        mapped = {}
        for csv_field, value in row.items():
            clean_field = csv_field.strip().lower().replace(" ", "_")
            db_field = field_map.get(clean_field, clean_field)
            mapped[db_field] = value.strip() if value else ""

        if mapped.get("name"):
            valid_fields = {k: v for k, v in mapped.items() if k in BusinessCreate.model_fields}
            await create_business(valid_fields)
            imported += 1

    return {"message": f"Imported {imported} businesses"}


@app.get("/api/businesses/export-csv")
async def export_csv():
    businesses = await get_all_businesses()
    if not businesses:
        return JSONResponse({"error": "No businesses to export"}, status_code=404)

    output = io.StringIO()
    fields = ["name", "name_en", "address", "city", "city_en", "postal_code", "region",
              "phone", "mobile", "email", "website", "category", "category_en",
              "description_gr", "description_en", "hours", "facebook", "instagram",
              "linkedin", "tax_id", "contact_person"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for biz in businesses:
        writer.writerow(biz)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=businesses.csv"},
    )


# --- Business detail routes (after CSV routes) ---

@app.get("/api/businesses/{business_id}")
async def get_business_detail(business_id: int):
    biz = await get_business(business_id)
    if not biz:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return biz


@app.put("/api/businesses/{business_id}")
async def update_business_route(business_id: int, data: BusinessUpdate):
    existing = await get_business(business_id)
    if not existing:
        return JSONResponse({"error": "Not found"}, status_code=404)
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    await update_business(business_id, update_data)
    return {"message": "Updated"}


@app.delete("/api/businesses/{business_id}")
async def delete_business_route(business_id: int):
    await delete_business(business_id)
    return {"message": "Deleted"}


# --- Submissions ---

@app.get("/api/submissions")
async def list_submissions():
    return await get_all_submissions()


@app.get("/api/submissions/{business_id}")
async def get_business_submissions(business_id: int):
    return await get_submissions(business_id)


@app.get("/api/directories")
async def list_directories():
    return DIRECTORIES


# --- Automation ---

@app.post("/api/automate")
async def start_automation(req: SubmissionRequest):
    global active_automation

    business = await get_business(req.business_id)
    if not business:
        return JSONResponse({"error": "Business not found"}, status_code=404)

    async def run_all():
        global active_automation
        for dir_id in req.directories:
            if dir_id not in AUTOMATION_MAP:
                continue

            await upsert_submission(req.business_id, dir_id, "running")
            await broadcast_sse({"directory_id": dir_id, "step": "start", "status": "running", "message": f"Starting {dir_id}..."})

            async def on_progress(event):
                await broadcast_sse({
                    "directory_id": event.directory_id,
                    "step": event.step,
                    "status": event.status,
                    "message": event.message,
                })

            automation = AUTOMATION_MAP[dir_id](on_progress=on_progress)
            active_automation = automation

            result = await automation.run(business)

            status = "submitted" if result.success else "error"
            await upsert_submission(req.business_id, dir_id, status, result.message, result.url)
            await broadcast_sse({
                "directory_id": dir_id,
                "step": "complete",
                "status": status,
                "message": result.message,
            })

        active_automation = None
        await broadcast_sse({"directory_id": "all", "step": "done", "status": "complete", "message": "All directories processed"})

    asyncio.create_task(run_all())
    return {"message": "Automation started"}


@app.post("/api/automate/continue")
async def continue_automation():
    global active_automation
    if active_automation:
        active_automation.resume_after_human()
        return {"message": "Resuming automation"}
    return JSONResponse({"error": "No active automation"}, status_code=400)


# --- SSE for live progress ---

async def broadcast_sse(data: dict):
    msg = f"data: {json.dumps(data)}\n\n"
    for queue in sse_queues:
        await queue.put(msg)


@app.get("/api/events")
async def sse_events():
    queue = asyncio.Queue()
    sse_queues.append(queue)

    async def event_generator():
        try:
            yield "data: {\"status\": \"connected\"}\n\n"
            while True:
                msg = await queue.get()
                yield msg
        except asyncio.CancelledError:
            pass
        finally:
            sse_queues.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# --- Serve frontend ---

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("static/index.html", "r") as f:
        return f.read()
