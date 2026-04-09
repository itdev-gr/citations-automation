import asyncio
import json
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .models import SubmissionRequest
from .supabase_db import get_business, upsert_submission, get_setting, save_setting
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
