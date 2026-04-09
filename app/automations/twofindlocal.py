from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class TwoFindLocalAutomation(BaseAutomation):
    directory_id = "twofindlocal"
    directory_name = "2FindLocal"
    registration_url = "https://www.2findlocal.com/add-business"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Business name
        await self.safe_fill(page, 'input[name="business_name"], input#business_name, input[name="name"]', business.get("name", ""))

        # Phone
        await self.safe_fill(page, 'input[name="phone"], input#phone', business.get("phone", ""))

        # Address
        await self.safe_fill(page, 'input[name="address"], input#address, input[name="street"]', business.get("address", ""))

        # City
        await self.safe_fill(page, 'input[name="city"], input#city', business.get("city", ""))

        # Zip
        await self.safe_fill(page, 'input[name="zip"], input[name="postal_code"], input#zip', business.get("postal_code", ""))

        # Country - select Greece
        await self.safe_select(page, 'select[name="country"], select#country', 'Greece')

        # Website
        await self.safe_fill(page, 'input[name="website"], input#website', business.get("website", ""))

        # Category
        category = business.get("category_en", "") or business.get("category", "")
        if category:
            await self.safe_fill(page, 'input[name="category"], input#category', category)
            await asyncio.sleep(1)
            await self.safe_click(page, '.autocomplete-suggestion:first-child, .ui-menu-item:first-child', timeout=2000)

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
