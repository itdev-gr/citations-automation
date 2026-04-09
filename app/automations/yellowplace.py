from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class YellowPlaceAutomation(BaseAutomation):
    directory_id = "yellowplace"
    directory_name = "Yellow.Place"
    registration_url = "https://yellow.place/en/add-place"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Close cookie banner
        await self.safe_click(page, '.cookie-accept, button:has-text("Accept"), #cookie-consent-accept', timeout=3000)

        # Business name
        await self.safe_fill(page, 'input[name="name"], input#name, input[placeholder*="name"]', business.get("name", ""))

        # Address
        await self.safe_fill(page, 'input[name="address"], input#address, input[placeholder*="address"]', business.get("address", ""))

        # City
        await self.safe_fill(page, 'input[name="city"], input#city', business.get("city", ""))

        # Postal code
        await self.safe_fill(page, 'input[name="zip"], input[name="postal_code"], input#zip', business.get("postal_code", ""))

        # Country - select Greece
        await self.safe_select(page, 'select[name="country"], select#country', 'GR')

        # Phone
        await self.safe_fill(page, 'input[name="phone"], input#phone', business.get("phone", ""))

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
            await self.safe_click(page, '.autocomplete-suggestion:first-child, .dropdown-item:first-child', timeout=2000)

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "Yellow.Place: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn, button:has-text("Add")')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Yellow.Place: Η επιχείρηση καταχωρήθηκε.",
            url="https://yellow.place",
        )
