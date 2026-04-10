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

        await asyncio.sleep(3)

        # Wait for editor to fully load — search input becomes enabled
        await self.emit("fill", "running", "Αναμονή φόρτωσης editor...")
        for _ in range(30):  # wait up to 30 seconds
            is_enabled = await page.evaluate("""
                () => {
                    const input = document.querySelector('input[type="text"][placeholder*="earch"], input[type="text"][name*="wz-text-input"]');
                    return input && !input.disabled;
                }
            """)
            if is_enabled:
                break
            await asyncio.sleep(1)

        # Search for the business location
        address = business.get("address", "") + " " + business.get("city", "")
        try:
            # Click on the search input first to focus it
            search_input = page.locator('input[type="text"]:not([disabled])').first
            await search_input.click(timeout=5000)
            await asyncio.sleep(0.5)
            await search_input.fill(address)
            await asyncio.sleep(2)
            # Press Enter to search
            await search_input.press("Enter")
            await asyncio.sleep(2)
            # Click first result if available
            await self.safe_click(page, '.search-results li:first-child, .result-item:first-child, .suggestion:first-child', timeout=5000)
            await asyncio.sleep(1)
        except Exception:
            await self.emit("fill", "running", "Δεν βρέθηκε search box, συνεχίζω...")

        # Add a place — this needs manual work in the Waze editor
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
