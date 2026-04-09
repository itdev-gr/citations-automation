import asyncio
import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .models import SubmissionRequest
from .supabase_db import get_business, upsert_submission
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

DIRECTORIES = [
    {"id": "xo_gr", "name": "Χρυσός Οδηγός (xo.gr)", "url": "https://www.xo.gr", "type": "Ελληνικός"},
    {"id": "vrisko", "name": "Vrisko.gr (11880)", "url": "https://www.vrisko.gr", "type": "Ελληνικός"},
    {"id": "europages", "name": "Europages", "url": "https://www.europages.gr", "type": "Ευρωπαϊκός"},
    {"id": "bing_places", "name": "Bing Places", "url": "https://www.bingplaces.com", "type": "Παγκόσμιος"},
    {"id": "foursquare", "name": "Foursquare", "url": "https://foursquare.com", "type": "Παγκόσμιος"},
    {"id": "apple_business", "name": "Apple Business Connect", "url": "https://businessconnect.apple.com", "type": "Παγκόσμιος"},
    {"id": "cybo", "name": "Cybo", "url": "https://www.cybo.com", "type": "Διεθνής"},
    {"id": "infobel", "name": "Infobel", "url": "https://www.infobel.com", "type": "Ευρωπαϊκός"},
]

# Global state for active automation
active_automation = None
sse_queues: list[asyncio.Queue] = []

app = FastAPI(title="Citations Automation Tool")

# Allow CORS from Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/api/directories")
async def list_directories():
    return DIRECTORIES


# --- Automation ---

@app.post("/api/automate")
async def start_automation(req: SubmissionRequest):
    global active_automation

    business = get_business(req.business_id)
    if not business:
        return JSONResponse({"error": "Business not found"}, status_code=404)

    async def run_all():
        global active_automation
        for dir_id in req.directories:
            if dir_id not in AUTOMATION_MAP:
                continue

            upsert_submission(req.business_id, dir_id, "running")
            await broadcast_sse({"directory_id": dir_id, "step": "start", "status": "running", "message": f"Εκκίνηση {dir_id}..."})

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
            upsert_submission(req.business_id, dir_id, status, result.message, result.url)
            await broadcast_sse({
                "directory_id": dir_id,
                "step": "complete",
                "status": status,
                "message": result.message,
            })

        active_automation = None
        await broadcast_sse({"directory_id": "all", "step": "done", "status": "complete", "message": "Όλοι οι κατάλογοι ολοκληρώθηκαν"})

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


# --- Serve frontend (static files at root for relative paths) ---

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("static/index.html", "r") as f:
        return f.read()

# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static"), name="static")
