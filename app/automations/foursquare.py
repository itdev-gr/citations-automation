from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult


class FoursquareAutomation(BaseAutomation):
    directory_id = "foursquare"
    directory_name = "Foursquare"
    registration_url = "https://foursquare.com/add-place"

    async def fill_form(self, page: Page, business: dict):
        await self.safe_fill(page, 'input[name="name"], input[name="venueName"], #venueName', business.get("name_en", "") or business.get("name", ""))
        await self.safe_fill(page, 'input[name="address"], #address', business.get("address", ""))
        await self.safe_fill(page, 'input[name="city"], #city', business.get("city_en", "") or business.get("city", ""))
        await self.safe_fill(page, 'input[name="zip"], input[name="postalCode"], #zip', business.get("postal_code", ""))
        await self.safe_fill(page, 'input[name="phone"], #phone', business.get("phone", ""))
        await self.safe_fill(page, 'input[name="url"], input[name="website"], #url', business.get("website", ""))

        # Try to type category
        category = business.get("category_en", "") or business.get("category", "")
        if category:
            await self.type_slowly(page, 'input[name="category"], input[name="primaryCategory"], #category', category)
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        await self.safe_click(page, 'button[type="submit"], input[type="submit"], button:has-text("Save"), button:has-text("Add")')
        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Foursquare: Place added. May need claim verification.",
            url="https://foursquare.com",
        )
