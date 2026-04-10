"""NAP Checker - Verify business NAP consistency across directories."""
import asyncio
import re
from playwright.async_api import async_playwright
from playwright_stealth import Stealth


# Directory search configs: how to find a business listing on each directory
DIRECTORY_SEARCH = {
    "xo_gr": {
        "search_url": "https://www.xo.gr/search/?what={name}&where={city}",
        "result_selector": ".result-title a, .listing-title a, h2 a",
    },
    "vrisko": {
        "search_url": "https://www.vrisko.gr/search/{name}/{city}",
        "result_selector": ".result-title a, .listing-title a, h3 a",
    },
    "brownbook": {
        "search_url": "https://www.brownbook.net/businesses/{name}+{city}/",
        "result_selector": ".business-name a, h2 a, .listing-title a",
    },
    "cybo": {
        "search_url": "https://www.cybo.com/search/?q={name}+{city}&loc=Greece",
        "result_selector": ".company-name a, h2 a, .listing-title a",
    },
    "foursquare": {
        "search_url": "https://foursquare.com/explore?near={city}&q={name}",
        "result_selector": ".venueTitle a, h2 a",
    },
    "tupalo": {
        "search_url": "https://www.tupalo.co/search?q={name}&where={city}",
        "result_selector": ".venue-name a, h3 a",
    },
    "globalcatalog": {
        "search_url": "https://www.globalcatalog.com/search.aspx?q={name}+{city}",
        "result_selector": ".company-name a, h3 a",
    },
    "showmelocal": {
        "search_url": "https://www.showmelocal.com/search?q={name}&loc={city}",
        "result_selector": ".business-name a, h3 a",
    },
    "trustpilot": {
        "search_url": "https://www.trustpilot.com/search?query={name}",
        "result_selector": ".business-unit-card a, h3 a",
    },
    "europages": {
        "search_url": "https://www.europages.co.uk/companies/{name}.html",
        "result_selector": ".company-name a, h3 a",
    },
}


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    # Remove extra whitespace, lowercase
    text = re.sub(r'\s+', ' ', text.strip().lower())
    # Remove common punctuation
    text = re.sub(r'[.,\-()\'"]', '', text)
    return text


def normalize_phone(phone: str) -> str:
    """Normalize phone for comparison — keep only digits."""
    if not phone:
        return ""
    return re.sub(r'[^\d]', '', phone)


def compare_field(expected: str, found: str) -> dict:
    """Compare two field values and return match info."""
    if not expected and not found:
        return {"status": "empty", "match": True}
    if not found:
        return {"status": "not_found", "match": False, "expected": expected, "found": ""}

    norm_expected = normalize_text(expected)
    norm_found = normalize_text(found)

    if norm_expected == norm_found:
        return {"status": "match", "match": True, "expected": expected, "found": found}

    # Partial match — one contains the other
    if norm_expected in norm_found or norm_found in norm_expected:
        return {"status": "partial", "match": False, "expected": expected, "found": found}

    return {"status": "mismatch", "match": False, "expected": expected, "found": found}


def compare_phone(expected: str, found: str) -> dict:
    """Compare phone numbers (digits only)."""
    if not expected and not found:
        return {"status": "empty", "match": True}
    if not found:
        return {"status": "not_found", "match": False, "expected": expected, "found": ""}

    norm_expected = normalize_phone(expected)
    norm_found = normalize_phone(found)

    if norm_expected == norm_found:
        return {"status": "match", "match": True, "expected": expected, "found": found}

    # Check if one is suffix of the other (country code difference)
    if norm_expected.endswith(norm_found[-10:]) or norm_found.endswith(norm_expected[-10:]):
        return {"status": "partial", "match": False, "expected": expected, "found": found}

    return {"status": "mismatch", "match": False, "expected": expected, "found": found}


async def check_directory(page, business: dict, dir_id: str, config: dict) -> dict:
    """Check one directory for NAP consistency."""
    from urllib.parse import quote_plus

    name = business.get("name_en") or business.get("name", "")
    city = business.get("city_en") or business.get("city", "")

    result = {
        "directory_id": dir_id,
        "found": False,
        "listing_url": "",
        "name": {"status": "not_checked", "match": False},
        "address": {"status": "not_checked", "match": False},
        "phone": {"status": "not_checked", "match": False},
    }

    try:
        url = config["search_url"].replace("{name}", quote_plus(name)).replace("{city}", quote_plus(city))
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(2)

        # Try to find the business in search results
        name_lower = name.lower()
        listing_url = await page.evaluate(f"""
            () => {{
                const name = "{name_lower.replace('"', '\\"')}";
                const links = document.querySelectorAll('{config["result_selector"]}');
                for (const link of links) {{
                    if (link.textContent.toLowerCase().includes(name) && link.href) {{
                        return link.href;
                    }}
                }}
                // Also check all links
                const allLinks = document.querySelectorAll('a');
                for (const link of allLinks) {{
                    if (link.textContent.toLowerCase().includes(name) && link.href && !link.href.includes('search')) {{
                        return link.href;
                    }}
                }}
                return null;
            }}
        """)

        if not listing_url:
            return result

        result["found"] = True
        result["listing_url"] = listing_url

        # Visit the listing page and extract NAP
        await page.goto(listing_url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(2)

        # Extract text content from the page
        page_text = await page.evaluate("""
            () => {
                return document.body.innerText;
            }
        """)

        # Extract structured data if available (JSON-LD, microdata)
        structured = await page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                for (const s of scripts) {
                    try {
                        const data = JSON.parse(s.textContent);
                        if (data['@type'] === 'LocalBusiness' || data['@type'] === 'Organization') {
                            return {
                                name: data.name || '',
                                address: data.address?.streetAddress || '',
                                phone: data.telephone || '',
                            };
                        }
                    } catch(e) {}
                }
                return null;
            }
        """)

        found_name = ""
        found_address = ""
        found_phone = ""

        if structured:
            found_name = structured.get("name", "")
            found_address = structured.get("address", "")
            found_phone = structured.get("phone", "")

        # If no structured data, try to extract from page text
        if not found_name:
            # Get the page title or first heading
            found_name = await page.evaluate("""
                () => {
                    const h1 = document.querySelector('h1');
                    return h1 ? h1.textContent.trim() : document.title.split('|')[0].split('-')[0].trim();
                }
            """)

        if not found_phone:
            # Try to find phone pattern in page
            phone_match = re.search(r'(?:\+30|0030)?\s*(?:2\d{2}|69\d)\s*\d{3}\s*\d{4}', page_text)
            if phone_match:
                found_phone = phone_match.group(0).strip()

        if not found_address:
            # Try common address selectors
            found_address = await page.evaluate("""
                () => {
                    const selectors = ['.address', '[itemprop="streetAddress"]', '.street-address'];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el) return el.textContent.trim();
                    }
                    return '';
                }
            """)

        # Compare
        expected_name = business.get("name", "")
        expected_address = business.get("address", "")
        expected_phone = business.get("phone", "")

        result["name"] = compare_field(expected_name, found_name)
        result["address"] = compare_field(expected_address, found_address)
        result["phone"] = compare_phone(expected_phone, found_phone)

    except Exception as e:
        result["error"] = str(e)

    return result


async def run_nap_check(business: dict, directory_ids: list, on_progress=None) -> list:
    """Run NAP check across multiple directories."""
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled', '--disable-dev-shm-usage'],
        )
        context = await browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="el-GR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        for dir_id in directory_ids:
            if dir_id not in DIRECTORY_SEARCH:
                results.append({
                    "directory_id": dir_id,
                    "found": False,
                    "name": {"status": "not_supported", "match": False},
                    "address": {"status": "not_supported", "match": False},
                    "phone": {"status": "not_supported", "match": False},
                })
                if on_progress:
                    await on_progress(dir_id, "skipped", f"{dir_id}: Δεν υποστηρίζεται ακόμα")
                continue

            if on_progress:
                await on_progress(dir_id, "checking", f"Έλεγχος {dir_id}...")

            config = DIRECTORY_SEARCH[dir_id]
            result = await check_directory(page, business, dir_id, config)
            results.append(result)

            if on_progress:
                status = "found" if result["found"] else "not_found"
                msg = f"{dir_id}: {'Βρέθηκε' if result['found'] else 'Δεν βρέθηκε'}"
                await on_progress(dir_id, status, msg)

        await browser.close()

    return results
