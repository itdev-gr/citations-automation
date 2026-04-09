from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class WazeAutomation(BaseAutomation):
    directory_id = "waze"
    directory_name = "Waze"
    registration_url = "https://www.waze.com/editor"

    async def fill_form(self, page: Page, business: dict):
        # Waze Map Editor requires login first
        await self.emit("login", "waiting_human",
            "Waze: Συνδεθείτε με τον λογαριασμό Waze/Google σας. Πατήστε 'Συνέχεια' όταν είστε μέσα.")
        self._human_event.clear()
        await self._human_event.wait()

        await asyncio.sleep(2)

        # Search for the business location
        address = business.get("address", "") + " " + business.get("city", "")
        search_box = page.locator('.search-input, input[placeholder*="Search"], #search-input')
        if await search_box.count() > 0:
            await search_box.first.fill(address)
            await asyncio.sleep(2)
            await self.safe_click(page, '.search-results li:first-child, .suggestion:first-child', timeout=3000)
            await asyncio.sleep(1)

        # Add a place
        await self.emit("fill", "waiting_human",
            "Waze: Προσθέστε την τοποθεσία χειροκίνητα στον χάρτη (Draw Place). "
            f"Όνομα: {business.get('name', '')}, Κατηγορία: {business.get('category', '')}. "
            "Πατήστε 'Συνέχεια' όταν ολοκληρώσετε.")
        self._human_event.clear()
        await self._human_event.wait()

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        # Save changes in Waze Editor
        await self.safe_click(page, 'button.save-button, .toolbar .save, [data-tooltip="Save"]', timeout=5000)
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Waze: Η τοποθεσία υποβλήθηκε για έγκριση.",
            url="https://www.waze.com",
        )
