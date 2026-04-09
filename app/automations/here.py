from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class HereAutomation(BaseAutomation):
    directory_id = "here"
    directory_name = "HERE WeGo"
    registration_url = "https://mapcreator.here.com/"

    async def fill_form(self, page: Page, business: dict):
        # HERE Map Creator requires login
        await self.emit("login", "waiting_human",
            "HERE: Συνδεθείτε με λογαριασμό HERE. Πατήστε 'Συνέχεια' μετά τη σύνδεση.")
        self._human_event.clear()
        await self._human_event.wait()

        await asyncio.sleep(2)

        # Search for location
        address = f"{business.get('address', '')}, {business.get('city', '')}"
        await self.safe_fill(page, 'input[type="search"], input[placeholder*="Search"], #search', address)
        await asyncio.sleep(2)
        await page.keyboard.press("Enter")
        await asyncio.sleep(2)

        # Add place
        await self.safe_click(page, 'button:has-text("Add"), button:has-text("Create"), .add-place-btn', timeout=5000)
        await asyncio.sleep(1)

        # Fill details
        await self.safe_fill(page, 'input[name="name"], #place-name', business.get("name", ""))
        await self.safe_fill(page, 'input[name="phone"], #place-phone', business.get("phone", ""))
        await self.safe_fill(page, 'input[name="website"], #place-website', business.get("website", ""))

        # Category
        category = business.get("category", "")
        if category:
            await self.safe_fill(page, 'input[name="category"], #place-category', category)
            await asyncio.sleep(1)
            await self.safe_click(page, '.dropdown-item:first-child, .suggestion:first-child', timeout=2000)

        await self.emit("fill", "waiting_human",
            f"HERE: Ελέγξτε τα στοιχεία: {business.get('name', '')}. Πατήστε 'Συνέχεια' για υποβολή.")
        self._human_event.clear()
        await self._human_event.wait()

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        await self.safe_click(page, 'button[type="submit"], button:has-text("Save"), button:has-text("Submit")')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="HERE: Τοποθεσία προστέθηκε στο Map Creator.",
            url="https://wego.here.com",
        )
