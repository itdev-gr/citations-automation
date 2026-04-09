from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult


class VriskoAutomation(BaseAutomation):
    directory_id = "vrisko"
    directory_name = "Vrisko.gr (11880)"
    registration_url = "https://vriskodigital.vrisko.gr/dorean-kataxorisi/"

    async def fill_form(self, page: Page, business: dict):
        await self.safe_fill(page, 'input[name="company"], input[name="name"], #company', business.get("name", ""))
        await self.safe_fill(page, 'input[name="phone"], input[name="tel"], #phone', business.get("phone", ""))
        await self.safe_fill(page, 'input[name="email"], #email', business.get("email", ""))
        await self.safe_fill(page, 'input[name="address"], #address', business.get("address", ""))
        await self.safe_fill(page, 'input[name="city"], #city', business.get("city", ""))
        await self.safe_fill(page, 'input[name="zip"], input[name="postal_code"], #zip', business.get("postal_code", ""))
        await self.safe_fill(page, 'input[name="website"], input[name="url"], #website', business.get("website", ""))
        await self.safe_fill(page, 'input[name="contact"], #contact', business.get("contact_person", ""))

        category = business.get("category", "")
        if category:
            await self.type_slowly(page, 'input[name="category"], input[name="sector"], #category', category)

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn')
        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Vrisko.gr: Form submitted. Check email for verification.",
            url="https://www.vrisko.gr",
        )
