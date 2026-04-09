from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class TrustpilotAutomation(BaseAutomation):
    directory_id = "trustpilot"
    directory_name = "Trustpilot"
    registration_url = "https://business.trustpilot.com/signup"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Close cookie popup
        await self.safe_click(page, '#onetrust-accept-btn-handler, button[id*="accept"]', timeout=3000)
        await asyncio.sleep(1)

        # Business signup form
        await self.safe_fill(page, 'input[name="companyName"], #companyName, input[placeholder*="company"]', business.get("name", ""))
        await self.safe_fill(page, 'input[name="website"], #website, input[name="domain"], input[placeholder*="website"]', business.get("website", ""))
        await self.safe_fill(page, 'input[name="email"], #email, input[placeholder*="email"]', business.get("email", ""))
        await self.safe_fill(page, 'input[name="firstName"], #firstName, input[placeholder*="First"]', business.get("contact_person", "").split(" ")[0] if business.get("contact_person") else "")

        contact = business.get("contact_person", "")
        if contact and " " in contact:
            await self.safe_fill(page, 'input[name="lastName"], #lastName, input[placeholder*="Last"]', contact.split(" ", 1)[1])

        await self.safe_fill(page, 'input[name="phone"], #phone, input[placeholder*="phone"]', business.get("phone", ""))

        # Country selector
        await self.safe_select(page, 'select[name="country"], #country', 'GR')

        await self.emit("fill", "waiting_human",
            f"Trustpilot: Ελέγξτε τη φόρμα εγγραφής για {business.get('name', '')}. "
            "Ορίστε κωδικό αν χρειάζεται. Πατήστε 'Συνέχεια'.")
        self._human_event.clear()
        await self._human_event.wait()

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "Trustpilot: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        await self.safe_click(page, 'button[type="submit"], input[type="submit"], button:has-text("Sign up"), button:has-text("Create")')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Trustpilot: Εγγραφή ολοκληρώθηκε. Ελέγξτε το email σας.",
            url="https://www.trustpilot.com",
        )
