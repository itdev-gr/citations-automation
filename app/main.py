import asyncio
import json
import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .models import SubmissionRequest
from .supabase_db import get_business, upsert_submission, get_setting, save_setting, get_submission
from .automations.xo_gr import XoGrAutomation
from .automations.vrisko import VriskoAutomation
from .automations.vres import VresAutomation
from .automations.findhere import FindHereAutomation
from .automations.stigmap import StigMapAutomation
from .automations.europages import EuropagesAutomation
from .automations.foursquare import FoursquareAutomation
from .automations.cybo import CyboAutomation
from .automations.infobel import InfobelAutomation
from .automations.waze import WazeAutomation
from .automations.tomtom import TomTomAutomation
from .automations.here import HereAutomation
from .automations.openstreetmap import OpenStreetMapAutomation
from .automations.tupalo import TupaloAutomation
from .automations.brownbook import BrownbookAutomation
from .automations.storeboard import StoreboardAutomation
from .automations.yellowplace import YellowPlaceAutomation
from .automations.showmelocal import ShowMeLocalAutomation
from .automations.globalcatalog import GlobalCatalogAutomation
from .automations.twofindlocal import TwoFindLocalAutomation
from .automations.trustpilot import TrustpilotAutomation
from .automations.citymaps import CityMapsAutomation

AUTOMATION_MAP = {
    "xo_gr": XoGrAutomation,
    "vrisko": VriskoAutomation,
    "vres": VresAutomation,
    "findhere": FindHereAutomation,
    "stigmap": StigMapAutomation,
    "waze": WazeAutomation,
    "tomtom": TomTomAutomation,
    "here": HereAutomation,
    "openstreetmap": OpenStreetMapAutomation,
    "foursquare": FoursquareAutomation,
    "tupalo": TupaloAutomation,
    "europages": EuropagesAutomation,
    "cybo": CyboAutomation,
    "infobel": InfobelAutomation,
    "brownbook": BrownbookAutomation,
    "storeboard": StoreboardAutomation,
    "yellowplace": YellowPlaceAutomation,
    "showmelocal": ShowMeLocalAutomation,
    "globalcatalog": GlobalCatalogAutomation,
    "twofindlocal": TwoFindLocalAutomation,
    "trustpilot": TrustpilotAutomation,
    "citymaps": CityMapsAutomation,
}

DIRECTORIES = [
    # Ελληνικοί
    {"id": "xo_gr", "name": "Χρυσός Οδηγός (xo.gr)", "url": "https://www.xo.gr", "type": "Ελληνικός"},
    {"id": "vrisko", "name": "Vrisko.gr (11880)", "url": "https://www.vrisko.gr", "type": "Ελληνικός"},
    {"id": "vres", "name": "Vres.gr", "url": "https://www.vres.gr", "type": "Ελληνικός"},
    {"id": "findhere", "name": "FindHere.gr", "url": "https://www.findhere.gr", "type": "Ελληνικός"},
    {"id": "stigmap", "name": "StigMap.gr", "url": "https://www.stigmap.gr", "type": "Ελληνικός"},
    # Χάρτες
    {"id": "waze", "name": "Waze", "url": "https://www.waze.com", "type": "Χάρτες"},
    {"id": "tomtom", "name": "TomTom", "url": "https://www.tomtom.com", "type": "Χάρτες"},
    {"id": "here", "name": "HERE WeGo", "url": "https://wego.here.com", "type": "Χάρτες"},
    {"id": "openstreetmap", "name": "OpenStreetMap", "url": "https://www.openstreetmap.org", "type": "Χάρτες"},
    # Reviews
    {"id": "foursquare", "name": "Foursquare", "url": "https://foursquare.com", "type": "Reviews"},
    {"id": "tupalo", "name": "Tupalo", "url": "https://www.tupalo.co", "type": "Reviews"},
    # Ευρωπαϊκοί / Διεθνείς
    {"id": "europages", "name": "Europages", "url": "https://www.europages.gr", "type": "Ευρωπαϊκός"},
    {"id": "cybo", "name": "Cybo", "url": "https://www.cybo.com", "type": "Διεθνής"},
    {"id": "infobel", "name": "Infobel", "url": "https://www.infobel.com", "type": "Ευρωπαϊκός"},
    {"id": "brownbook", "name": "Brownbook.net", "url": "https://www.brownbook.net", "type": "Διεθνής"},
    {"id": "storeboard", "name": "Storeboard", "url": "https://www.storeboard.com", "type": "Διεθνής"},
    {"id": "yellowplace", "name": "Yellow.Place", "url": "https://yellow.place", "type": "Διεθνής"},
    {"id": "showmelocal", "name": "ShowMeLocal", "url": "https://www.showmelocal.com", "type": "Διεθνής"},
    {"id": "globalcatalog", "name": "GlobalCatalog", "url": "https://www.globalcatalog.com", "type": "Διεθνής"},
    {"id": "twofindlocal", "name": "2FindLocal", "url": "https://www.2findlocal.com", "type": "Διεθνής"},
    {"id": "trustpilot", "name": "Trustpilot", "url": "https://www.trustpilot.com", "type": "Reviews"},
    {"id": "citymaps", "name": "CityMaps.gr", "url": "https://citymaps.gr", "type": "Ελληνικός"},
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



@app.on_event("startup")
async def load_settings():
    """Load 2Captcha API key from Supabase on startup."""
    key = get_setting("twocaptcha_api_key")
    if key:
        os.environ["TWOCAPTCHA_API_KEY"] = key


class SettingUpdate(BaseModel):
    key: str
    value: str


@app.get("/api/directories")
async def list_directories():
    return DIRECTORIES


@app.post("/api/settings")
async def update_setting(s: SettingUpdate):
    save_setting(s.key, s.value)
    if s.key == "twocaptcha_api_key":
        os.environ["TWOCAPTCHA_API_KEY"] = s.value
    return {"message": "Setting saved"}


@app.get("/api/settings/{key}")
async def read_setting(key: str):
    val = get_setting(key)
    return {"key": key, "value": val or ""}


# --- NAP Checker ---

class NapCheckRequest(BaseModel):
    business_id: int
    directories: list[str] = []

@app.post("/api/nap-check")
async def start_nap_check(req: NapCheckRequest):
    from .nap_checker import run_nap_check
    from .supabase_db import _request

    business = get_business(req.business_id)
    if not business:
        return JSONResponse({"error": "Business not found"}, status_code=404)

    # If no directories specified, use all submitted ones
    dir_ids = req.directories
    if not dir_ids:
        subs = _request("citations_submissions",
                        filters=f"business_id=eq.{req.business_id}&status=eq.submitted")
        dir_ids = [s["directory_id"] for s in (subs or [])]

    if not dir_ids:
        return JSONResponse({"error": "Δεν υπάρχουν υποβληθέντες κατάλογοι"}, status_code=400)

    async def on_progress(dir_id, status, message):
        await broadcast_sse({
            "directory_id": dir_id,
            "step": "nap_check",
            "status": status,
            "message": message,
        })

    async def run_check():
        await broadcast_sse({"directory_id": "nap", "step": "start", "status": "running", "message": "Ξεκινάει NAP έλεγχος..."})
        results = await run_nap_check(business, dir_ids, on_progress=on_progress)
        await broadcast_sse({"directory_id": "nap", "step": "done", "status": "complete", "message": "NAP έλεγχος ολοκληρώθηκε", "results": results})

    asyncio.create_task(run_check())
    return {"message": "NAP check started", "directories": dir_ids}


# --- Automation ---

@app.post("/api/automate")
async def start_automation(req: SubmissionRequest):
    global active_automation

    business = get_business(req.business_id)
    if not business:
        return JSONResponse({"error": "Business not found"}, status_code=404)

    async def run_all():
        global active_automation

        # Load proxies from settings
        proxy_list_raw = get_setting("proxy_list") or ""
        proxies = [p.strip() for p in proxy_list_raw.split("\n") if p.strip()]

        results_summary = []

        for dir_id in req.directories:
            if dir_id not in AUTOMATION_MAP:
                continue

            # Internal duplicate check — skip if already submitted
            existing = get_submission(req.business_id, dir_id)
            if existing and existing.get("status") == "submitted":
                await broadcast_sse({
                    "directory_id": dir_id, "step": "complete",
                    "status": "already_listed",
                    "message": "Έχει ήδη υποβληθεί.",
                    "url": existing.get("url", ""),
                })
                results_summary.append({"dir": dir_id, "status": "already_listed"})
                continue

            upsert_submission(req.business_id, dir_id, "running")
            await broadcast_sse({"directory_id": dir_id, "step": "start", "status": "running", "message": f"Εκκίνηση {dir_id}..."})

            try:
                async def on_progress(event):
                    await broadcast_sse({
                        "directory_id": event.directory_id,
                        "step": event.step,
                        "status": event.status,
                        "message": event.message,
                    })

                automation = AUTOMATION_MAP[dir_id](on_progress=on_progress)
                active_automation = automation

                # Pick a random proxy if available
                proxy = random.choice(proxies) if proxies else None

                result = await automation.run(business, proxy=proxy)

                # Determine status
                if result.message and "Υπάρχει ήδη" in result.message:
                    status = "already_listed"
                elif result.success:
                    status = "submitted"
                else:
                    status = "error"

                upsert_submission(req.business_id, dir_id, status, result.message, result.url)

                await broadcast_sse({
                    "directory_id": dir_id,
                    "step": "complete",
                    "status": status,
                    "message": result.message,
                    "url": result.url,
                    "screenshot": result.screenshot,
                })
                results_summary.append({"dir": dir_id, "status": status, "message": result.message})

            except Exception as e:
                error_msg = f"Σφάλμα: {str(e)}"
                upsert_submission(req.business_id, dir_id, "error", error_msg)
                await broadcast_sse({
                    "directory_id": dir_id,
                    "step": "complete",
                    "status": "error",
                    "message": error_msg,
                })
                results_summary.append({"dir": dir_id, "status": "error", "message": error_msg})
                # Continue to next directory!

        active_automation = None
        await broadcast_sse({"directory_id": "all", "step": "done", "status": "complete", "message": "Όλοι οι κατάλογοι ολοκληρώθηκαν"})

        # Send email notification
        await send_completion_email(business, results_summary)

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


# --- Email notification ---

async def send_completion_email(business: dict, results: list):
    """Send email when all submissions complete."""
    smtp_host = get_setting("smtp_host")
    smtp_port = get_setting("smtp_port")
    smtp_user = get_setting("smtp_user")
    smtp_pass = get_setting("smtp_password")
    notify_email = get_setting("notify_email")

    if not all([smtp_host, smtp_user, smtp_pass, notify_email]):
        return  # Email not configured

    try:
        biz_name = business.get("name", "Unknown")
        submitted = sum(1 for r in results if r["status"] == "submitted")
        already = sum(1 for r in results if r["status"] == "already_listed")
        errors = sum(1 for r in results if r["status"] == "error")

        body = f"""Ολοκληρώθηκε η υποβολή για: {biz_name}

Αποτελέσματα:
  Υποβλήθηκαν: {submitted}
  Ήδη υπάρχουν: {already}
  Σφάλματα: {errors}

Λεπτομέρειες:
"""
        for r in results:
            status_icon = {"submitted": "✓", "already_listed": "≡", "error": "✗"}.get(r["status"], "?")
            body += f"  {status_icon} {r['dir']}: {r.get('message', r['status'])}\n"

        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = notify_email
        msg["Subject"] = f"Citations: {biz_name} — {submitted} υποβολές, {errors} σφάλματα"
        msg.attach(MIMEText(body, "plain", "utf-8"))

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: _send_email(smtp_host, int(smtp_port or 587), smtp_user, smtp_pass, msg))
    except Exception as e:
        print(f"Email error: {e}")


def _send_email(host, port, user, password, msg):
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)


# --- Screenshots ---

@app.get("/api/screenshots/{filename}")
async def get_screenshot(filename: str):
    path = f"/opt/citations/screenshots/{filename}"
    if os.path.exists(path):
        return FileResponse(path, media_type="image/png")
    return JSONResponse({"error": "Not found"}, status_code=404)


# --- Report export ---

@app.get("/api/report/{business_id}")
async def export_report(business_id: int):
    """Export CSV report of all submissions for a business."""
    from .supabase_db import _request
    business = get_business(business_id)
    if not business:
        return JSONResponse({"error": "Business not found"}, status_code=404)

    subs = _request("citations_submissions", filters=f"business_id=eq.{business_id}")
    if not subs:
        subs = []

    # Build CSV
    lines = ["Directory,Status,Notes,URL,Date"]
    for s in subs:
        dir_name = s.get("directory_id", "")
        status = s.get("status", "")
        notes = (s.get("notes", "") or "").replace(",", ";").replace("\n", " ")
        url = s.get("url", "") or ""
        date = s.get("submitted_at", s.get("updated_at", "")) or ""
        lines.append(f"{dir_name},{status},{notes},{url},{date}")

    csv_content = "\n".join(lines)
    biz_name = business.get("name", "business").replace(" ", "_")

    return StreamingResponse(
        iter(["\ufeff" + csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=report_{biz_name}.csv"},
    )


# --- Serve frontend (static files at root for relative paths) ---

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("static/index.html", "r") as f:
        return f.read()

# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static"), name="static")
