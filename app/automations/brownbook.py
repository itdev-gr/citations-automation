from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class BrownbookAutomation(BaseAutomation):
    directory_id = "brownbook"
    directory_name = "Brownbook.net"
    registration_url = "https://www.brownbook.net/add-business/"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Close cookie banner
        await self.safe_click(page, '.cookie-accept, #accept-cookies, button:has-text("Accept")', timeout=3000)

        # Business name
        await self.safe_fill(page, 'input[name="business_name"], input#business_name, input[name="name"]', business.get("name", ""))

        # Phone
        await self.safe_fill(page, 'input[name="phone"], input#phone', business.get("phone", ""))

        # Email
        await self.safe_fill(page, 'input[name="email"], input#email', business.get("email", ""))

        # Address
        await self.safe_fill(page, 'input[name="address"], input#address, input[name="street"]', business.get("address", ""))

        # City
        await self.safe_fill(page, 'input[name="city"], input#city', business.get("city", ""))

        # Postal code
        await self.safe_fill(page, 'input[name="zip"], input[name="postal_code"], input#zip', business.get("postal_code", ""))

        # Country - select Greece
        await self.safe_select(page, 'select[name="country"], select#country', 'Greece')
        await asyncio.sleep(0.5)

        # Website
        await self.safe_fill(page, 'input[name="website"], input#website', business.get("website", ""))

        # Description
        desc = business.get("description_en", "") or business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, 'textarea[name="description"], textarea#description', desc)

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
                "Brownbook: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Brownbook.net: Η επιχείρηση καταχωρήθηκε.",
            url="https://www.brownbook.net",
        )
