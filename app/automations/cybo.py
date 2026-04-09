from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult


class CyboAutomation(BaseAutomation):
    directory_id = "cybo"
    directory_name = "Cybo"
    registration_url = "https://www.cybo.com/add-business"

    async def fill_form(self, page: Page, business: dict):
        name = business.get("name_en", "") or business.get("name", "")
        await self.safe_fill(page, 'input[name="name"], input[name="business_name"], #name', name)
        await self.safe_fill(page, 'input[name="phone"], #phone', business.get("phone", ""))
        await self.safe_fill(page, 'input[name="email"], #email', business.get("email", ""))
        await self.safe_fill(page, 'input[name="address"], #address', business.get("address", ""))
        await self.safe_fill(page, 'input[name="city"], #city', business.get("city_en", "") or business.get("city", ""))
        await self.safe_fill(page, 'input[name="zip"], input[name="postal_code"], #zip', business.get("postal_code", ""))
        await self.safe_fill(page, 'input[name="website"], input[name="url"], #website', business.get("website", ""))

        desc = business.get("description_en", "") or business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, 'textarea[name="description"], #description', desc)

        # Country
        await self.safe_select(page, 'select[name="country"], #country', "GR")

        category = business.get("category_en", "") or business.get("category", "")
        if category:
            await self.type_slowly(page, 'input[name="category"], #category', category)

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        await self.safe_click(page, 'button[type="submit"], input[type="submit"]')
        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Cybo: Business submitted. Verification may be required.",
            url="https://www.cybo.com",
        )
