from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class FindHereAutomation(BaseAutomation):
    directory_id = "findhere"
    directory_name = "FindHere.gr"
    registration_url = "https://www.findhere.gr/add-business/"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Close cookie banner
        await self.safe_click(page, '.cookie-accept, #accept-cookies, button:has-text("Αποδοχή")', timeout=3000)

        # Business name
        await self.safe_fill(page, 'input[name="business_name"], input[name="name"], #business_name', business.get("name", ""), field_name="Επωνυμία")

        # Category
        category = business.get("category", "")
        if category:
            await self.type_slowly(page, 'input[name="category"], #category', category, field_name="Κατηγορία")
            await asyncio.sleep(1)
            await self.safe_click(page, '.autocomplete-suggestion:first-child, .ui-menu-item:first-child', timeout=2000)

        # Phone
        await self.safe_fill(page, 'input[name="phone"], #phone', business.get("phone", ""), field_name="Τηλέφωνο")

        # Email
        email_filled = await self.safe_fill(page, 'input[name="email"], #email', business.get("email", ""), field_name="Email")
        if not email_filled and business.get("email"):
            await self.emit("fill", "running", "ΠΡΟΣΟΧΗ: Το πεδίο email δεν βρέθηκε!")

        # Address
        await self.safe_fill(page, 'input[name="address"], #address', business.get("address", ""), field_name="Διεύθυνση")

        # City
        await self.safe_fill(page, 'input[name="city"], #city', business.get("city", ""), field_name="Πόλη")

        # Postal code
        await self.safe_fill(page, 'input[name="postal_code"], input[name="zipcode"], #postal_code', business.get("postal_code", ""), field_name="Τ.Κ.")

        # Website
        await self.safe_fill(page, 'input[name="website"], #website', business.get("website", ""), field_name="Website")

        # Description
        desc = business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, 'textarea[name="description"], #description', desc, field_name="Περιγραφή")

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "FindHere.gr: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        url_before = page.url

        clicked = await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn')
        if not clicked:
            return AutomationResult(
                success=False,
                directory_id=self.directory_id,
                message=f"FindHere.gr: Δεν βρέθηκε το κουμπί υποβολής. {self.field_summary()}",
            )

        await asyncio.sleep(5)

        result = await self.verify_submission(
            page, url_before,
            success_indicators=["Ευχαριστούμε", "επιτυχ", "ολοκληρώθηκε", ".success", ".alert-success"],
            error_indicators=[".error", ".alert-danger", "υποχρεωτικό", "απαιτείται"],
        )

        return AutomationResult(
            success=result["success"],
            directory_id=self.directory_id,
            message=f"FindHere.gr: {result['message']} {self.field_summary()}",
            url=page.url if result["success"] else "",
        )
