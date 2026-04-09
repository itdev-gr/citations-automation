from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class NapFinderAutomation(BaseAutomation):
    directory_id = "napfinder"
    directory_name = "NAP Finder"
    registration_url = "https://www.napfinder.com/add-business"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Close cookie banner
        await self.safe_click(page, '.cookie-accept, #accept-cookies, button:has-text("Accept")', timeout=3000)

        # Business name
        await self.safe_fill(page, 'input[name="name"], input[name="business_name"], #name, #business_name', business.get("name", ""))

        # Phone
        await self.safe_fill(page, 'input[name="phone"], #phone', business.get("phone", ""))

        # Email
        await self.safe_fill(page, 'input[name="email"], #email', business.get("email", ""))

        # Address
        await self.safe_fill(page, 'input[name="address"], #address, input[name="street"]', business.get("address", ""))

        # City
        await self.safe_fill(page, 'input[name="city"], #city', business.get("city", ""))

        # Postal code
        await self.safe_fill(page, 'input[name="zip"], input[name="postal_code"], #zip', business.get("postal_code", ""))

        # Country
        await self.safe_select(page, 'select[name="country"], select#country', 'Greece')

        # Website
        await self.safe_fill(page, 'input[name="website"], #website', business.get("website", ""))

        # Description
        desc = business.get("description_en", "") or business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, 'textarea[name="description"], textarea#description', desc)

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "NAP Finder: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="NAP Finder: Η επιχείρηση καταχωρήθηκε.",
            url="https://www.napfinder.com",
        )
