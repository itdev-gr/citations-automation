from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class BingPlacesAutomation(BaseAutomation):
    directory_id = "bing_places"
    directory_name = "Bing Places"
    registration_url = "https://www.bingplaces.com/"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)
        await page.wait_for_load_state('networkidle', timeout=10000)

        # Bing Places requires Microsoft account login
        current_url = page.url
        if 'login' in current_url or 'microsoft' in current_url or 'live.com' in current_url:
            await self.pause_for_human(
                "Bing Places: Συνδεθείτε με τον Microsoft λογαριασμό σας. Πατήστε 'Συνέχεια' αφού μπείτε."
            )
            await asyncio.sleep(2)

        # Try Google import option first
        try:
            await self.emit("fill", "running", "Bing Places: Ψάχνω για import από Google...")
            import_btn = page.locator('text="Import from Google", a:has-text("Google"), button:has-text("Import")')
            if await import_btn.count() > 0:
                await import_btn.first.click()
                await self.pause_for_human(
                    "Bing Places: Πατήστε 'Import from Google My Business' και συνδεθείτε στο Google. "
                    "Πατήστε 'Συνέχεια' όταν ολοκληρωθεί."
                )
                return
        except Exception:
            pass

        # Manual: try "Add new business" or "Claim"
        try:
            add_btn = page.locator('text="Add", a:has-text("New"), button:has-text("Add new")')
            if await add_btn.count() > 0:
                await add_btn.first.click()
                await asyncio.sleep(2)
        except Exception:
            pass

        # Fill form fields
        await self.safe_fill(page, 'input[name="businessName"], input[name="name"], #businessName', business.get("name", ""))
        await self.safe_fill(page, 'input[name="phone"], input[name="phoneNumber"], #phone', business.get("phone", ""))
        await self.safe_fill(page, 'input[name="address"], input[name="addressLine1"], #address', business.get("address", ""))
        await self.safe_fill(page, 'input[name="city"], #city', business.get("city", ""))
        await self.safe_fill(page, 'input[name="zip"], input[name="postalCode"], #zip', business.get("postal_code", ""))
        await self.safe_fill(page, 'input[name="website"], input[name="url"], #website', business.get("website", ""))

        category = business.get("category_en", "") or business.get("category", "")
        if category:
            await self.type_slowly(page, 'input[name="category"], input[name="businessCategory"]', category)
            await asyncio.sleep(1)
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        await self.pause_for_human(
            "Bing Places: Ελέγξτε τα στοιχεία και ολοκληρώστε τη διαδικασία. Πατήστε 'Συνέχεια'."
        )

        await self.safe_click(page, 'button[type="submit"], input[type="submit"], button:has-text("Submit"), button:has-text("Save")')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Bing Places: Ολοκληρώθηκε. Μπορεί να χρειαστεί verification.",
            url="https://www.bingplaces.com",
        )
