from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult


class AppleBusinessAutomation(BaseAutomation):
    directory_id = "apple_business"
    directory_name = "Apple Business Connect"
    registration_url = "https://businessconnect.apple.com/"

    async def fill_form(self, page: Page, business: dict):
        # Apple Business Connect requires Apple ID login first
        await self.emit("fill", "waiting_human",
            "Apple Business Connect requires Apple ID login. Please sign in, then click Continue.")
        self._human_event.clear()
        await self._human_event.wait()

        await self.emit("fill", "running", "Searching for your business...")

        # Search for the business
        name = business.get("name_en", "") or business.get("name", "")
        await self.type_slowly(page, 'input[type="search"], input[name="search"], input[placeholder*="Search"]', name)
        await page.keyboard.press("Enter")

        await self.emit("fill", "waiting_human",
            "Select your business from the results, or click 'Add new' if not found. Then click Continue in the dashboard.")

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Apple Business Connect: Complete the claim process in the browser.",
            url="https://businessconnect.apple.com",
        )
