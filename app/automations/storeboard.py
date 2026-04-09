from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class StoreboardAutomation(BaseAutomation):
    directory_id = "storeboard"
    directory_name = "Storeboard"
    registration_url = "https://www.storeboard.com/register"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Close cookie banner
        await self.safe_click(page, '.cookie-accept, button:has-text("Accept")', timeout=3000)

        # Look for "Business" registration option
        await self.safe_click(page, 'a:has-text("Business"), button:has-text("Business"), .business-signup', timeout=3000)
        await asyncio.sleep(1)

        # Business name
        await self.safe_fill(page, 'input[name="BusinessName"], input#BusinessName, input[name="name"]', business.get("name", ""))

        # Email
        await self.safe_fill(page, 'input[name="Email"], input#Email, input[name="email"]', business.get("email", ""))

        # Phone
        await self.safe_fill(page, 'input[name="Phone"], input#Phone, input[name="phone"]', business.get("phone", ""))

        # Address
        await self.safe_fill(page, 'input[name="Address"], input#Address, input[name="address"]', business.get("address", ""))

        # City
        await self.safe_fill(page, 'input[name="City"], input#City, input[name="city"]', business.get("city", ""))

        # Postal code
        await self.safe_fill(page, 'input[name="ZipCode"], input#ZipCode, input[name="zip"]', business.get("postal_code", ""))

        # Country
        await self.safe_select(page, 'select[name="Country"], select#Country', 'Greece')

        # Website
        await self.safe_fill(page, 'input[name="Website"], input#Website, input[name="website"]', business.get("website", ""))

        # Description
        desc = business.get("description_en", "") or business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, 'textarea[name="Description"], textarea#Description', desc)

        # Password field - notify human
        await self.emit("fill", "waiting_human",
            f"Storeboard: Ελέγξτε τα στοιχεία και ορίστε κωδικό. Πατήστε 'Συνέχεια'.")
        self._human_event.clear()
        await self._human_event.wait()

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "Storeboard: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn, #register-btn')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Storeboard: Εγγραφή ολοκληρώθηκε. Ελέγξτε το email σας.",
            url="https://www.storeboard.com",
        )
