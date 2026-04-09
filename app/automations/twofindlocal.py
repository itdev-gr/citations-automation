from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class TwoFindLocalAutomation(BaseAutomation):
    directory_id = "twofindlocal"
    directory_name = "2FindLocal"
    registration_url = "https://www.2findlocal.com/Modules/Biz/bizPhoneLookup.php"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Step 1: Phone lookup
        phone = business.get("phone", "")
        await self.safe_fill(page, '#searchKeyword, input[name="phone"]', phone)
        await self.safe_click(page, '#submit, button.btnPL', timeout=3000)
        await asyncio.sleep(3)

        # After phone lookup, the form loads dynamically
        # Fill business details
        await self.safe_fill(page, 'input[name="business_name"], input[name="name"]', business.get("name", ""))
        await self.safe_fill(page, 'input[name="address"], input[name="street"]', business.get("address", ""))
        await self.safe_fill(page, 'input[name="city"]', business.get("city", ""))
        await self.safe_fill(page, 'input[name="zip"], input[name="postal_code"]', business.get("postal_code", ""))
        await self.safe_fill(page, 'input[name="website"]', business.get("website", ""))

        # Category
        category = business.get("category_en", "") or business.get("category", "")
        if category:
            await self.safe_fill(page, 'input[name="category"]', category)

        # If form didn't load, pause for human
        await self.emit("fill", "waiting_human",
            f"2FindLocal: Ελέγξτε/συμπληρώστε τα στοιχεία για {business.get('name', '')}. Πατήστε 'Συνέχεια'.")
        self._human_event.clear()
        await self._human_event.wait()

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "2FindLocal: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="2FindLocal: Η επιχείρηση καταχωρήθηκε.",
            url="https://www.2findlocal.com",
        )
