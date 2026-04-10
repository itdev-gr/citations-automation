import asyncio
import json
import os
import random
import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

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
from .automations.waze import WazeAutomation
from .automations.tomtom import TomTomAutomation
from .automations.here import HereAutomation
from .automations.openstreetmap import OpenStreetMapAutomation
from .automations.tupalo import TupaloAutomation
from .automations.brownbook import BrownbookAutomation
from .automations.storeboard import StoreboardAutomation
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
    "brownbook": BrownbookAutomation,
    "storeboard": StoreboardAutomation,
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
    {"id": "brownbook", "name": "Brownbook.net", "url": "https://www.brownbook.net", "type": "Διεθνής"},
    {"id": "storeboard", "name": "Storeboard", "url": "https://www.storeboard.com", "type": "Διεθνής"},
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


# --- Google Business Profile Import ---

class GoogleCallbackRequest(BaseModel):
    code: str
    redirect_uri: str

class GoogleImportRequest(BaseModel):
    access_token: str
    locations: list[str]


@app.post("/api/google/callback")
async def google_callback(req: GoogleCallbackRequest):
    """Exchange auth code for access token, then list all GBP locations."""
    client_id = get_setting("google_client_id")
    client_secret = get_setting("google_client_secret")

    if not client_id or not client_secret:
        return JSONResponse({"error": "Google OAuth credentials not configured"}, status_code=400)

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_res = await client.post("https://oauth2.googleapis.com/token", data={
            "code": req.code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": req.redirect_uri,
            "grant_type": "authorization_code",
        })

    if token_res.status_code != 200:
        return JSONResponse({"error": f"Token exchange failed: {token_res.text}"}, status_code=400)

    tokens = token_res.json()
    access_token = tokens.get("access_token")
    if not access_token:
        return JSONResponse({"error": "No access token received"}, status_code=400)

    # List accounts
    businesses = []
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}

        acct_res = await client.get(
            "https://mybusinessaccountmanagement.googleapis.com/v1/accounts",
            headers=headers,
        )
        if acct_res.status_code != 200:
            return JSONResponse({"error": f"Failed to list accounts: {acct_res.text}"}, status_code=400)

        accounts = acct_res.json().get("accounts", [])

        for account in accounts:
            account_name = account["name"]  # e.g. "accounts/123"

            # List locations for this account
            loc_res = await client.get(
                f"https://mybusinessbusinessinformation.googleapis.com/v1/{account_name}/locations",
                headers=headers,
                params={"readMask": "name,title,storefrontAddress,phoneNumbers,websiteUri,categories,profile,regularHours"},
            )
            if loc_res.status_code != 200:
                continue

            locations = loc_res.json().get("locations", [])
            for loc in locations:
                addr = loc.get("storefrontAddress", {})
                phones = loc.get("phoneNumbers", {})
                cat = loc.get("categories", {}).get("primaryCategory", {})
                businesses.append({
                    "location_id": loc.get("name", ""),
                    "title": loc.get("title", ""),
                    "name": loc.get("title", ""),
                    "address": ", ".join(addr.get("addressLines", [])),
                    "city": addr.get("locality", ""),
                    "postal_code": addr.get("postalCode", ""),
                    "region": addr.get("administrativeArea", ""),
                    "phone": phones.get("primaryPhone", ""),
                    "mobile": (phones.get("additionalPhones") or [""])[0],
                    "website": loc.get("websiteUri", ""),
                    "category": cat.get("displayName", ""),
                    "description": (loc.get("profile") or {}).get("description", ""),
                    "hours": _format_gbp_hours(loc.get("regularHours", {})),
                })

    return {"access_token": access_token, "businesses": businesses}


@app.post("/api/google/import")
async def google_import(req: GoogleImportRequest):
    """Fetch full location data for selected locations and upsert to Supabase."""
    from .supabase_db import _request

    imported = 0
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {req.access_token}"}

        for loc_id in req.locations:
            # Fetch full location data
            loc_res = await client.get(
                f"https://mybusinessbusinessinformation.googleapis.com/v1/{loc_id}",
                headers=headers,
                params={"readMask": "name,title,storefrontAddress,phoneNumbers,websiteUri,categories,profile,regularHours"},
            )
            if loc_res.status_code != 200:
                continue

            loc = loc_res.json()
            addr = loc.get("storefrontAddress", {})
            phones = loc.get("phoneNumbers", {})
            cat = loc.get("categories", {}).get("primaryCategory", {})
            description = (loc.get("profile") or {}).get("description", "")

            biz_data = {
                "name": loc.get("title", ""),
                "name_en": loc.get("title", ""),
                "address": ", ".join(addr.get("addressLines", [])),
                "city": addr.get("locality", ""),
                "city_en": addr.get("locality", ""),
                "postal_code": addr.get("postalCode", ""),
                "region": addr.get("administrativeArea", ""),
                "phone": phones.get("primaryPhone", ""),
                "mobile": (phones.get("additionalPhones") or [""])[0],
                "website": loc.get("websiteUri", ""),
                "category": cat.get("displayName", ""),
                "category_en": cat.get("displayName", ""),
                "description_gr": description,
                "description_en": description,
                "hours": _format_gbp_hours(loc.get("regularHours", {})),
            }

            # Remove empty values
            biz_data = {k: v for k, v in biz_data.items() if v}

            if biz_data.get("name"):
                _request("citations_businesses", method="POST", body=biz_data)
                imported += 1

    return {"imported": imported}


def _format_gbp_hours(regular_hours: dict) -> str:
    """Format GBP regularHours periods into a readable string."""
    periods = regular_hours.get("periods", [])
    if not periods:
        return ""

    day_names = {
        "MONDAY": "Δευ", "TUESDAY": "Τρι", "WEDNESDAY": "Τετ",
        "THURSDAY": "Πεμ", "FRIDAY": "Παρ", "SATURDAY": "Σαβ", "SUNDAY": "Κυρ",
    }
    lines = []
    for p in periods:
        day = day_names.get(p.get("openDay", ""), p.get("openDay", ""))
        open_time = p.get("openTime", {})
        close_time = p.get("closeTime", {})
        open_str = f"{open_time.get('hours', 0):02d}:{open_time.get('minutes', 0):02d}"
        close_str = f"{close_time.get('hours', 0):02d}:{close_time.get('minutes', 0):02d}"
        lines.append(f"{day} {open_str}-{close_str}")

    return ", ".join(lines)


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
