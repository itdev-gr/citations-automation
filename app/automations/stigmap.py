from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class StigMapAutomation(BaseAutomation):
    directory_id = "stigmap"
    directory_name = "StigMap.gr"
    registration_url = "https://www.stigmap.gr/"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Close cookie banner
        await self.safe_click(page, '.cookie-accept, #accept-cookies, button:has-text("Αποδοχή")', timeout=3000)

        # Look for add business link/button
        await self.safe_click(page, 'a:has-text("Καταχώρηση"), a:has-text("Προσθήκη"), a:has-text("Εγγραφή"), a[href*="add"], a[href*="register"]', timeout=5000)
        await asyncio.sleep(2)

        # Business name
        await self.safe_fill(page, 'input[name="name"], input[name="business_name"], #name, #business_name', business.get("name", ""), field_name="Επωνυμία")

        # Category
        category = business.get("category", "")
        if category:
            await self.safe_fill(page, 'input[name="category"], #category, select[name="category"]', category, field_name="Κατηγορία")

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

        # Website
        await self.safe_fill(page, 'input[name="website"], #website', business.get("website", ""), field_name="Website")

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "StigMap.gr: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        url_before = page.url

        clicked = await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn')
        if not clicked:
            return AutomationResult(
                success=False,
                directory_id=self.directory_id,
                message=f"StigMap.gr: Δεν βρέθηκε το κουμπί υποβολής. {self.field_summary()}",
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
            message=f"StigMap.gr: {result['message']} {self.field_summary()}",
            url=page.url if result["success"] else "",
        )
