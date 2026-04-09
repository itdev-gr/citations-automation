from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class InfobelAutomation(BaseAutomation):
    directory_id = "infobel"
    directory_name = "Infobel"
    registration_url = "https://www.infobelpro.com/en/promote-products/list-my-business"

    async def fill_form(self, page: Page, business: dict):
        # InfobelPRO is the business listing page
        await asyncio.sleep(3)
        await page.wait_for_load_state('networkidle', timeout=15000)

        # Fill whatever form fields are available
        name = business.get("name_en", "") or business.get("name", "")
        await self.safe_fill(page, 'input[name="companyName"], input[name="name"], input[name="business_name"]', name)
        await self.safe_fill(page, 'input[name="phone"], input[name="telephone"], input[type="tel"]', business.get("phone", ""))
        await self.safe_fill(page, 'input[name="email"], input[type="email"]', business.get("email", ""))
        await self.safe_fill(page, 'input[name="address"], input[name="street"]', business.get("address", ""))

        city = business.get("city_en", "") or business.get("city", "")
        await self.safe_fill(page, 'input[name="city"], input[name="locality"]', city)
        await self.safe_fill(page, 'input[name="zipCode"], input[name="postalCode"]', business.get("postal_code", ""))
        await self.safe_fill(page, 'input[name="website"], input[name="url"]', business.get("website", ""))

        desc = business.get("description_en", "") or business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, 'textarea[name="description"]', desc[:1000])

        # Country
        await self.safe_select(page, 'select[name="country"]', "GR")

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        await self.pause_for_human(
            "Infobel: Συμπληρώστε τα υπόλοιπα στοιχεία και υποβάλετε. Πατήστε 'Συνέχεια' όταν τελειώσετε."
        )

        await self.safe_click(page, 'button[type="submit"], input[type="submit"], a:has-text("Submit"), button:has-text("Submit")')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Infobel: Ολοκληρώθηκε.",
            url="https://www.infobelpro.com",
        )
