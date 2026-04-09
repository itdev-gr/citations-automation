from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class FindHereAutomation(BaseAutomation):
    directory_id = "findhere"
    directory_name = "FindHere.gr"
    registration_url = "https://www.findhere.gr/add-business/"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Close cookie banner
        await self.safe_click(page, '.cookie-accept, #accept-cookies, button:has-text("Αποδοχή")', timeout=3000)

        # Business name
        await self.safe_fill(page, 'input[name="business_name"], input[name="name"], #business_name', business.get("name", ""))

        # Category
        category = business.get("category", "")
        if category:
            await self.type_slowly(page, 'input[name="category"], #category', category)
            await asyncio.sleep(1)
            await self.safe_click(page, '.autocomplete-suggestion:first-child, .ui-menu-item:first-child', timeout=2000)

        # Phone
        await self.safe_fill(page, 'input[name="phone"], #phone', business.get("phone", ""))

        # Email
        await self.safe_fill(page, 'input[name="email"], #email', business.get("email", ""))

        # Address
        await self.safe_fill(page, 'input[name="address"], #address', business.get("address", ""))

        # City
        await self.safe_fill(page, 'input[name="city"], #city', business.get("city", ""))

        # Postal code
        await self.safe_fill(page, 'input[name="postal_code"], input[name="zipcode"], #postal_code', business.get("postal_code", ""))

        # Website
        await self.safe_fill(page, 'input[name="website"], #website', business.get("website", ""))

        # Description
        desc = business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, 'textarea[name="description"], #description', desc)

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "FindHere.gr: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="FindHere.gr: Φόρμα υποβλήθηκε.",
            url="https://www.findhere.gr",
        )
