from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class TripAdvisorAutomation(BaseAutomation):
    directory_id = "tripadvisor"
    directory_name = "TripAdvisor"
    registration_url = "https://www.tripadvisor.com/Owners"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Close cookie popup
        await self.safe_click(page, '#onetrust-accept-btn-handler, button[id*="accept"]', timeout=3000)
        await asyncio.sleep(1)

        # TripAdvisor Owners - search for business or add new listing
        # First try to search for existing listing
        search_input = page.locator('input[type="search"], input[placeholder*="business"], #search-input, input[name="q"]')
        if await search_input.count() > 0:
            name = business.get("name", "")
            city = business.get("city", "")
            await search_input.first.fill(f"{name} {city}")
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
            await asyncio.sleep(3)

        # If no listing found, look for "Add a new listing" link
        await self.safe_click(page, 'a:has-text("list your business"), a:has-text("Get Listed"), a:has-text("Add"), button:has-text("Get Listed")', timeout=5000)
        await asyncio.sleep(2)

        # Fill business details
        await self.safe_fill(page, 'input[name="businessName"], #businessName', business.get("name", ""))
        await self.safe_fill(page, 'input[name="address"], #address, input[name="street"]', business.get("address", ""))
        await self.safe_fill(page, 'input[name="city"], #city', business.get("city", ""))
        await self.safe_fill(page, 'input[name="postalCode"], #postalCode, input[name="zip"]', business.get("postal_code", ""))
        await self.safe_fill(page, 'input[name="phone"], #phone', business.get("phone", ""))
        await self.safe_fill(page, 'input[name="email"], #email', business.get("email", ""))
        await self.safe_fill(page, 'input[name="website"], #website', business.get("website", ""))

        # Country - select Greece
        await self.safe_select(page, 'select[name="country"], #country', 'GR')

        await self.emit("fill", "waiting_human",
            f"TripAdvisor: Ελέγξτε τα στοιχεία για {business.get('name', '')}. "
            "Συμπληρώστε τυχόν πεδία που λείπουν. Πατήστε 'Συνέχεια'.")
        self._human_event.clear()
        await self._human_event.wait()

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "TripAdvisor: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        await self.safe_click(page, 'button[type="submit"], input[type="submit"], button:has-text("Submit")')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="TripAdvisor: Αίτημα καταχώρισης υποβλήθηκε.",
            url="https://www.tripadvisor.com",
        )
