from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class VresAutomation(BaseAutomation):
    directory_id = "vres"
    directory_name = "Vres.gr"
    registration_url = "https://www.vres.gr/GoldPages/Company/FreeRegister"

    async def fill_form(self, page: Page, business: dict):
        # Company name
        await self.safe_fill(page, '#CompanyName', business.get("name", ""), field_name="Επωνυμία")

        # Category / Activity
        category = business.get("category", "")
        if category:
            await self.type_slowly(page, '#Activity', category, field_name="Κατηγορία")
            await asyncio.sleep(1)
            await self.safe_click(page, '.ui-autocomplete .ui-menu-item:first-child, .autocomplete-suggestion:first-child', timeout=2000)

        # Address
        await self.safe_fill(page, '#Address', business.get("address", ""), field_name="Διεύθυνση")

        # City
        await self.safe_fill(page, '#City', business.get("city", ""), field_name="Πόλη")

        # Postal code
        await self.safe_fill(page, '#PostalCode', business.get("postal_code", ""), field_name="Τ.Κ.")

        # Phone
        await self.safe_fill(page, '#Phone', business.get("phone", ""), field_name="Τηλέφωνο")

        # Mobile
        await self.safe_fill(page, '#Mobile', business.get("mobile", ""), field_name="Κινητό")

        # Email
        email_filled = await self.safe_fill(page, '#Email', business.get("email", ""), field_name="Email")
        if not email_filled and business.get("email"):
            await self.emit("fill", "running", "ΠΡΟΣΟΧΗ: Το πεδίο email δεν βρέθηκε!")

        # Website
        await self.safe_fill(page, '#Website', business.get("website", ""), field_name="Website")

        # Description
        desc = business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, '#Description', desc, field_name="Περιγραφή")

        # Contact person
        await self.safe_fill(page, '#ContactName', business.get("contact_person", ""), field_name="Υπεύθυνος")

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        # Handle CAPTCHA
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "Vres.gr: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        # Accept terms if checkbox exists
        await self.safe_click(page, '#AcceptTerms, input[name="AcceptTerms"]', timeout=2000)

        url_before = page.url

        # Submit
        clicked = await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn, #submitBtn')
        if not clicked:
            return AutomationResult(
                success=False,
                directory_id=self.directory_id,
                message=f"Vres.gr: Δεν βρέθηκε το κουμπί υποβολής. {self.field_summary()}",
            )

        await asyncio.sleep(5)

        result = await self.verify_submission(
            page, url_before,
            success_indicators=["Ευχαριστούμε", "επιτυχ", "ολοκληρώθηκε", ".success", ".alert-success"],
            error_indicators=[".field-validation-error", ".alert-danger", "υποχρεωτικό", "απαιτείται"],
        )

        return AutomationResult(
            success=result["success"],
            directory_id=self.directory_id,
            message=f"Vres.gr: {result['message']} {self.field_summary()}",
            url=page.url if result["success"] else "",
        )
