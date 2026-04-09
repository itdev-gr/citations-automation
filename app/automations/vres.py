from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class VresAutomation(BaseAutomation):
    directory_id = "vres"
    directory_name = "Vres.gr"
    registration_url = "https://www.vres.gr/GoldPages/Company/FreeRegister"

    async def fill_form(self, page: Page, business: dict):
        # Company name
        await self.safe_fill(page, '#CompanyName', business.get("name", ""))

        # Category / Activity
        category = business.get("category", "")
        if category:
            await self.type_slowly(page, '#Activity', category)
            await asyncio.sleep(1)
            await self.safe_click(page, '.ui-autocomplete .ui-menu-item:first-child, .autocomplete-suggestion:first-child', timeout=2000)

        # Address
        await self.safe_fill(page, '#Address', business.get("address", ""))

        # City
        await self.safe_fill(page, '#City', business.get("city", ""))

        # Postal code
        await self.safe_fill(page, '#PostalCode', business.get("postal_code", ""))

        # Phone
        await self.safe_fill(page, '#Phone', business.get("phone", ""))

        # Mobile
        await self.safe_fill(page, '#Mobile', business.get("mobile", ""))

        # Email
        await self.safe_fill(page, '#Email', business.get("email", ""))

        # Website
        await self.safe_fill(page, '#Website', business.get("website", ""))

        # Description
        desc = business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, '#Description', desc)

        # Contact person
        await self.safe_fill(page, '#ContactName', business.get("contact_person", ""))

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        # Handle CAPTCHA
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "Vres.gr: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        # Accept terms if checkbox exists
        await self.safe_click(page, '#AcceptTerms, input[name="AcceptTerms"]', timeout=2000)

        # Submit
        await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn, #submitBtn')

        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Vres.gr: Φόρμα υποβλήθηκε. Ελέγξτε το email σας.",
            url="https://www.vres.gr",
        )
