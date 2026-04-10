from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class GlobalCatalogAutomation(BaseAutomation):
    directory_id = "globalcatalog"
    directory_name = "GlobalCatalog"
    registration_url = "https://www.globalcatalog.com/add-business.html"
    search_url = "https://www.globalcatalog.com/search.aspx?q={name}+{city}"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Business name
        await self.safe_fill(page, 'input[name="company"], input#company, input[name="name"]', business.get("name", ""))

        # Phone
        await self.safe_fill(page, 'input[name="phone"], input#phone', business.get("phone", ""))

        # Email
        await self.safe_fill(page, 'input[name="email"], input#email', business.get("email", ""))

        # Address
        await self.safe_fill(page, 'input[name="address"], input#address, input[name="street"]', business.get("address", ""))

        # City
        await self.safe_fill(page, 'input[name="city"], input#city', business.get("city", ""))

        # Country - select Greece
        await self.safe_select(page, 'select[name="country"], select#country', 'Greece')

        # Website
        await self.safe_fill(page, 'input[name="website"], input#website, input[name="url"]', business.get("website", ""))

        # Description
        desc = business.get("description_en", "") or business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, 'textarea[name="description"], textarea#description', desc)

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "GlobalCatalog: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="GlobalCatalog: Η επιχείρηση καταχωρήθηκε.",
            url="https://www.globalcatalog.com",
        )
