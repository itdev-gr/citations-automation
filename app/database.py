import aiosqlite
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "citations.db")

DIRECTORIES = [
    {"id": "xo_gr", "name": "Χρυσός Οδηγός (xo.gr)", "url": "https://www.xo.gr", "type": "Greek"},
    {"id": "vrisko", "name": "Vrisko.gr (11880)", "url": "https://www.vrisko.gr", "type": "Greek"},
    {"id": "europages", "name": "Europages", "url": "https://www.europages.gr", "type": "European"},
    {"id": "bing_places", "name": "Bing Places", "url": "https://www.bingplaces.com", "type": "Global"},
    {"id": "foursquare", "name": "Foursquare", "url": "https://foursquare.com", "type": "Global"},
    {"id": "apple_business", "name": "Apple Business Connect", "url": "https://businessconnect.apple.com", "type": "Global"},
    {"id": "cybo", "name": "Cybo", "url": "https://www.cybo.com", "type": "International"},
]


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_en TEXT,
            address TEXT,
            city TEXT,
            city_en TEXT,
            postal_code TEXT,
            region TEXT,
            phone TEXT,
            mobile TEXT,
            email TEXT,
            website TEXT,
            category TEXT,
            category_en TEXT,
            description_gr TEXT,
            description_en TEXT,
            hours TEXT,
            facebook TEXT,
            instagram TEXT,
            linkedin TEXT,
            logo_path TEXT,
            tax_id TEXT,
            contact_person TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            directory_id TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            submitted_at TEXT,
            notes TEXT,
            url TEXT,
            FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE,
            UNIQUE(business_id, directory_id)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    await db.commit()
    await db.close()


async def get_all_businesses():
    db = await get_db()
    cursor = await db.execute("SELECT * FROM businesses ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    await db.close()
    return [dict(row) for row in rows]


async def get_business(business_id: int):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM businesses WHERE id = ?", (business_id,))
    row = await cursor.fetchone()
    await db.close()
    return dict(row) if row else None


async def create_business(data: dict) -> int:
    db = await get_db()
    fields = [k for k in data.keys() if k != "id"]
    placeholders = ", ".join(["?"] * len(fields))
    columns = ", ".join(fields)
    values = [data[k] for k in fields]
    cursor = await db.execute(
        f"INSERT INTO businesses ({columns}) VALUES ({placeholders})", values
    )
    await db.commit()
    business_id = cursor.lastrowid
    await db.close()
    return business_id


async def update_business(business_id: int, data: dict):
    db = await get_db()
    fields = [k for k in data.keys() if k not in ("id", "created_at")]
    sets = ", ".join([f"{k} = ?" for k in fields])
    values = [data[k] for k in fields] + [business_id]
    await db.execute(
        f"UPDATE businesses SET {sets}, updated_at = datetime('now') WHERE id = ?",
        values,
    )
    await db.commit()
    await db.close()


async def delete_business(business_id: int):
    db = await get_db()
    await db.execute("DELETE FROM submissions WHERE business_id = ?", (business_id,))
    await db.execute("DELETE FROM businesses WHERE id = ?", (business_id,))
    await db.commit()
    await db.close()


async def get_submissions(business_id: int):
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM submissions WHERE business_id = ?", (business_id,)
    )
    rows = await cursor.fetchall()
    await db.close()
    return [dict(row) for row in rows]


async def get_all_submissions():
    db = await get_db()
    cursor = await db.execute("SELECT * FROM submissions ORDER BY business_id")
    rows = await cursor.fetchall()
    await db.close()
    return [dict(row) for row in rows]


async def upsert_submission(business_id: int, directory_id: str, status: str, notes: str = "", url: str = ""):
    db = await get_db()
    await db.execute("""
        INSERT INTO submissions (business_id, directory_id, status, submitted_at, notes, url)
        VALUES (?, ?, ?, datetime('now'), ?, ?)
        ON CONFLICT(business_id, directory_id)
        DO UPDATE SET status = ?, submitted_at = datetime('now'), notes = ?, url = ?
    """, (business_id, directory_id, status, notes, url, status, notes, url))
    await db.commit()
    await db.close()


async def get_setting(key: str, default: str = ""):
    db = await get_db()
    cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = await cursor.fetchone()
    await db.close()
    return row["value"] if row else default


async def set_setting(key: str, value: str):
    db = await get_db()
    await db.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
    )
    await db.commit()
    await db.close()
