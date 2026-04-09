from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult


class InfobelAutomation(BaseAutomation):
    directory_id = "infobel"
    directory_name = "Infobel"
    registration_url = "https://www.infobel.com/en/greece"

    async def fill_form(self, page: Page, business: dict):
        # Infobel may require searching for the business first
        name = business.get("name_en", "") or business.get("name", "")

        await self.emit("fill", "running", "Searching for business on Infobel...")

        # Try search
        await self.safe_fill(page, 'input[name="q"], input[name="what"], input[type="search"], #search', name)
        city = business.get("city_en", "") or business.get("city", "")
        await self.safe_fill(page, 'input[name="where"], input[name="location"], #where', city)
        await self.safe_click(page, 'button[type="submit"], input[type="submit"], .search-btn')

        await self.emit("fill", "waiting_human",
            "Infobel: Search complete. If your business appears, click 'Claim'. If not, look for 'Add business' option. Then click Continue.")

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Infobel: Complete the process in the browser.",
            url="https://www.infobel.com",
        )
