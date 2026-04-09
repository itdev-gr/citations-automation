"""Supabase database client for the local automation server."""
import os
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode

SUPABASE_URL = "https://jkbxdjuszhrnbvivsuvw.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImprYnhkanVzemhybmJ2aXZzdXZ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU2MzkyNjQsImV4cCI6MjA5MTIxNTI2NH0.GziMKhOwRiUHlvgckD4FQgk39DHrXDKt-lY-atdjGnM"

HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
}


def _request(table, method="GET", filters="", body=None, extra_headers=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if filters:
        url += f"?{filters}"

    headers = {**HEADERS}
    if extra_headers:
        headers.update(extra_headers)

    if method == "POST":
        headers["Prefer"] = "return=representation"
    elif method in ("PATCH", "PUT"):
        headers["Prefer"] = "return=representation"
    elif method == "DELETE":
        headers["Prefer"] = "return=minimal"

    data = json.dumps(body).encode() if body else None
    req = Request(url, data=data, headers=headers, method=method)

    try:
        with urlopen(req) as resp:
            if method == "DELETE":
                return []
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"Supabase error: {e}")
        return []


def get_business(business_id: int):
    result = _request("citations_businesses", filters=f"id=eq.{business_id}")
    return result[0] if result else None


def upsert_submission(business_id: int, directory_id: str, status: str, notes: str = "", url: str = ""):
    """Upsert a submission record."""
    body = {
        "business_id": business_id,
        "directory_id": directory_id,
        "status": status,
        "notes": notes,
        "url": url,
    }
    # Try to update first
    existing = _request("citations_submissions",
                        filters=f"business_id=eq.{business_id}&directory_id=eq.{directory_id}")
    if existing:
        _request("citations_submissions", method="PATCH",
                 filters=f"business_id=eq.{business_id}&directory_id=eq.{directory_id}",
                 body={"status": status, "notes": notes, "url": url})
    else:
        _request("citations_submissions", method="POST", body=body)
