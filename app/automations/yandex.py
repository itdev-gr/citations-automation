from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class YandexAutomation(BaseAutomation):
    directory_id = "yandex"
    directory_name = "Yandex Maps"
    registration_url = "https://yandex.com/sprav/"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Yandex Business requires login
        await self.emit("login", "waiting_human",
            "Yandex: Συνδεθείτε με λογαριασμό Yandex. Πατήστε 'Συνέχεια' μετά τη σύνδεση.")
        self._human_event.clear()
        await self._human_event.wait()

        await asyncio.sleep(2)

        # Add organization
        await self.safe_click(page, 'a:has-text("Add"), button:has-text("Add organization"), a:has-text("New")', timeout=5000)
        await asyncio.sleep(2)

        # Fill form
        await self.safe_fill(page, 'input[name="name"], #org-name, input[placeholder*="Organization"]', business.get("name", ""))
        await self.safe_fill(page, 'input[name="address"], #address', f"{business.get('address', '')}, {business.get('city', '')}, Greece")
        await self.safe_fill(page, 'input[name="phone"], #phone', business.get("phone", ""))
        await self.safe_fill(page, 'input[name="website"], #website', business.get("website", ""))

        # Category
        category = business.get("category", "")
        if category:
            await self.safe_fill(page, 'input[name="rubric"], #rubric, input[placeholder*="category"]', category)
            await asyncio.sleep(1)
            await self.safe_click(page, '.suggest-item:first-child, .dropdown-item:first-child', timeout=2000)

        await self.emit("fill", "waiting_human",
            f"Yandex: Ελέγξτε τα στοιχεία για {business.get('name', '')}. Πατήστε 'Συνέχεια'.")
        self._human_event.clear()
        await self._human_event.wait()

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        await self.safe_click(page, 'button[type="submit"], button:has-text("Save"), button:has-text("Submit"), button:has-text("Publish")')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Yandex: Η επιχείρηση υποβλήθηκε στο Yandex Maps.",
            url="https://yandex.com/maps",
        )
