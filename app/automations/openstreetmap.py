from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class OpenStreetMapAutomation(BaseAutomation):
    directory_id = "openstreetmap"
    directory_name = "OpenStreetMap"
    registration_url = "https://www.openstreetmap.org/"

    async def fill_form(self, page: Page, business: dict):
        # OSM requires login
        await self.emit("login", "waiting_human",
            "OpenStreetMap: Συνδεθείτε με λογαριασμό OSM. Πατήστε 'Συνέχεια' μετά τη σύνδεση.")
        self._human_event.clear()
        await self._human_event.wait()

        await asyncio.sleep(2)

        # Search for location
        address = f"{business.get('address', '')}, {business.get('city', '')}, Greece"
        await self.safe_fill(page, '#query, input[name="query"]', address)
        await page.keyboard.press("Enter")
        await asyncio.sleep(3)

        # Open editor (iD editor)
        await self.safe_click(page, '#editanchor, a:has-text("Edit")', timeout=5000)
        await asyncio.sleep(3)

        # In iD editor: Add a point
        await self.safe_click(page, 'button.add-point, .point-button, button[title*="Point"]', timeout=5000)
        await asyncio.sleep(1)

        # User needs to click on map to place the point
        await self.emit("fill", "waiting_human",
            f"OpenStreetMap: Κάντε κλικ στον χάρτη για να τοποθετήσετε το σημείο. "
            f"Στη συνέχεια συμπληρώστε: Όνομα: {business.get('name', '')}, "
            f"Τηλ: {business.get('phone', '')}, Website: {business.get('website', '')}. "
            "Πατήστε 'Συνέχεια' όταν είστε έτοιμοι.")
        self._human_event.clear()
        await self._human_event.wait()

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        # Save in iD editor
        await self.safe_click(page, 'button.save, #save-button, button:has-text("Save")', timeout=5000)
        await asyncio.sleep(2)

        # Add changeset comment
        comment = f"Add business: {business.get('name', '')}"
        await self.safe_fill(page, '#preset-input-comment, textarea.changeset-comment', comment)

        # Upload
        await self.safe_click(page, 'button.action:has-text("Upload"), button#upload, button:has-text("Upload")', timeout=5000)
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="OpenStreetMap: Η τοποθεσία προστέθηκε.",
            url="https://www.openstreetmap.org",
        )
