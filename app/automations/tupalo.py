from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class TupaloAutomation(BaseAutomation):
    directory_id = "tupalo"
    directory_name = "Tupalo"
    registration_url = "https://www.tupalo.co/spot/new"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Close cookie banner
        await self.safe_click(page, '.cookie-accept, #accept-cookies, button:has-text("Accept")', timeout=3000)

        # Tupalo may require login first
        login_check = page.locator('a:has-text("Log in"), a:has-text("Sign in")')
        if await login_check.count() > 0:
            await self.emit("login", "waiting_human",
                "Tupalo: Συνδεθείτε ή δημιουργήστε λογαριασμό. Πατήστε 'Συνέχεια' μετά τη σύνδεση.")
            self._human_event.clear()
            await self._human_event.wait()
            await asyncio.sleep(2)

        # Business name
        await self.safe_fill(page, 'input[name="spot[name]"], input#spot_name, input[name="name"]', business.get("name", ""))

        # Address
        await self.safe_fill(page, 'input[name="spot[street]"], input#spot_street, input[name="address"]', business.get("address", ""))

        # City
        await self.safe_fill(page, 'input[name="spot[city]"], input#spot_city, input[name="city"]', business.get("city", ""))

        # Postal code
        await self.safe_fill(page, 'input[name="spot[zip]"], input#spot_zip, input[name="zip"]', business.get("postal_code", ""))

        # Country
        await self.safe_select(page, 'select[name="spot[country]"], select#spot_country', 'GR')

        # Phone
        await self.safe_fill(page, 'input[name="spot[phone]"], input#spot_phone, input[name="phone"]', business.get("phone", ""))

        # Website
        await self.safe_fill(page, 'input[name="spot[website]"], input#spot_website, input[name="website"]', business.get("website", ""))

        # Description
        desc = business.get("description_en", "") or business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, 'textarea[name="spot[description]"], textarea#spot_description, textarea[name="description"]', desc)

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        await self.safe_click(page, 'button[type="submit"], input[type="submit"], input[name="commit"]')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Tupalo: Η επιχείρηση καταχωρήθηκε.",
            url="https://www.tupalo.co",
        )
