from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult


class XoGrAutomation(BaseAutomation):
    directory_id = "xo_gr"
    directory_name = "Χρυσός Οδηγός (xo.gr)"
    registration_url = "https://www.xo.gr/dorean-katachorisi/"

    async def fill_form(self, page: Page, business: dict):
        # XO.gr free registration form
        await self.safe_fill(page, 'input[name="company_name"], input[name="eponymia"], #company_name', business.get("name", ""))
        await self.safe_fill(page, 'input[name="phone"], input[name="tilefono"], #phone', business.get("phone", ""))
        await self.safe_fill(page, 'input[name="mobile"], #mobile', business.get("mobile", ""))
        await self.safe_fill(page, 'input[name="email"], #email', business.get("email", ""))
        await self.safe_fill(page, 'input[name="address"], input[name="dieuthinsi"], #address', business.get("address", ""))
        await self.safe_fill(page, 'input[name="city"], input[name="poli"], #city', business.get("city", ""))
        await self.safe_fill(page, 'input[name="postal_code"], input[name="tk"], #postal_code', business.get("postal_code", ""))
        await self.safe_fill(page, 'input[name="website"], input[name="url"], #website', business.get("website", ""))
        await self.safe_fill(page, 'input[name="contact_person"], input[name="contact"], #contact_person', business.get("contact_person", ""))

        # Category - try typing it for autocomplete
        category = business.get("category", "")
        if category:
            await self.type_slowly(page, 'input[name="category"], input[name="drastiriotita"], #category', category)

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        # Look for submit button
        await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn, #submit')
        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="XO.gr: Form submitted. Check email for verification.",
            url="https://www.xo.gr",
        )
