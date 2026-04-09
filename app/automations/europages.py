from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult


class EuropagesAutomation(BaseAutomation):
    directory_id = "europages"
    directory_name = "Europages"
    registration_url = "https://www.europages.co.uk/register.html"

    async def fill_form(self, page: Page, business: dict):
        await self.safe_fill(page, 'input[name="companyName"], #companyName', business.get("name_en", "") or business.get("name", ""))
        await self.safe_fill(page, 'input[name="phone"], input[name="telephone"], #phone', business.get("phone", ""))
        await self.safe_fill(page, 'input[name="email"], #email', business.get("email", ""))
        await self.safe_fill(page, 'input[name="address"], input[name="street"], #address', business.get("address", ""))
        await self.safe_fill(page, 'input[name="city"], #city', business.get("city_en", "") or business.get("city", ""))
        await self.safe_fill(page, 'input[name="zipCode"], input[name="postalCode"], #zipCode', business.get("postal_code", ""))
        await self.safe_fill(page, 'input[name="website"], input[name="url"], #website', business.get("website", ""))
        await self.safe_fill(page, 'input[name="firstName"], #firstName', business.get("contact_person", "").split()[0] if business.get("contact_person") else "")
        await self.safe_fill(page, 'input[name="lastName"], #lastName', " ".join(business.get("contact_person", "").split()[1:]) if business.get("contact_person") else "")

        desc = business.get("description_en", "") or business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, 'textarea[name="description"], textarea[name="activity"], #description', desc)

        # Try to select Greece as country
        await self.safe_select(page, 'select[name="country"], #country', "GR")

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        await self.safe_click(page, 'button[type="submit"], input[type="submit"]')
        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Europages: Form submitted. Email verification required.",
            url="https://www.europages.co.uk",
        )
