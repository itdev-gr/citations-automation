from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class TomTomAutomation(BaseAutomation):
    directory_id = "tomtom"
    directory_name = "TomTom"
    registration_url = "https://www.tomtom.com/mapshare/tools/"

    async def fill_form(self, page: Page, business: dict):
        # TomTom MapShare - report a map change / add a place
        await asyncio.sleep(2)

        # Close cookie banner
        await self.safe_click(page, '#onetrust-accept-btn-handler, .cookie-accept, button[id*="accept"]', timeout=3000)
        await asyncio.sleep(1)

        # Look for "Report a map change" or "Add a missing place"
        await self.safe_click(page, 'a[href*="report"], button:has-text("Report"), a:has-text("missing place"), a:has-text("Add")', timeout=5000)
        await asyncio.sleep(2)

        # Search for location
        address = f"{business.get('address', '')}, {business.get('city', '')}, Greece"
        await self.safe_fill(page, 'input[type="search"], input[placeholder*="Search"], #search-input', address)
        await asyncio.sleep(2)
        await self.safe_click(page, '.search-results li:first-child, .suggestion:first-child', timeout=3000)
        await asyncio.sleep(1)

        # Fill POI details
        await self.safe_fill(page, 'input[name="name"], #poi-name, input[placeholder*="Name"]', business.get("name", ""))
        await self.safe_fill(page, 'input[name="phone"], #poi-phone, input[placeholder*="Phone"]', business.get("phone", ""))

        # If form is complex, pause for human
        await self.emit("fill", "waiting_human",
            f"TomTom: Ελέγξτε/συμπληρώστε τα στοιχεία: {business.get('name', '')}. "
            "Πατήστε 'Συνέχεια' για υποβολή.")
        self._human_event.clear()
        await self._human_event.wait()

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        await self.safe_click(page, 'button[type="submit"], button:has-text("Submit"), button:has-text("Send"), .submit-btn')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="TomTom: Αναφορά υποβλήθηκε για αλλαγή χάρτη.",
            url="https://www.tomtom.com",
        )
