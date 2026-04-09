from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult


class BingPlacesAutomation(BaseAutomation):
    directory_id = "bing_places"
    directory_name = "Bing Places"
    registration_url = "https://www.bingplaces.com/"

    async def fill_form(self, page: Page, business: dict):
        # Bing Places has an "Import from Google" option - try that first
        await self.emit("fill", "running", "Bing Places: Looking for Google import option...")

        try:
            import_btn = await page.wait_for_selector(
                'text="Import from Google", a:has-text("Google"), button:has-text("Import")',
                timeout=5000
            )
            if import_btn:
                await import_btn.click()
                await self.emit("fill", "waiting_human",
                    "Bing Places: Click 'Import from Google My Business' and sign in with your Google account.")
                return
        except Exception:
            pass

        # Manual fill fallback
        await self.safe_fill(page, 'input[name="businessName"], #businessName', business.get("name", ""))
        await self.safe_fill(page, 'input[name="phone"], #phone', business.get("phone", ""))
        await self.safe_fill(page, 'input[name="address"], #address', business.get("address", ""))
        await self.safe_fill(page, 'input[name="city"], #city', business.get("city", ""))
        await self.safe_fill(page, 'input[name="zip"], #zip', business.get("postal_code", ""))
        await self.safe_fill(page, 'input[name="website"], #website', business.get("website", ""))

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Bing Places: Complete the import/registration in the browser.",
            url="https://www.bingplaces.com",
        )
