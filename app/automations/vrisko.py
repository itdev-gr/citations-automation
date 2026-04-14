from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class VriskoAutomation(BaseAutomation):
    directory_id = "vrisko"
    directory_name = "Vrisko.gr (11880)"
    registration_url = "https://vriskodigital.vrisko.gr/dorean-kataxorisi/"

    async def fill_form(self, page: Page, business: dict):
        # Company name (required)
        await self.safe_fill(page, '#GeneralInfoStep_CompanyName', business.get("name", ""), field_name="Επωνυμία")

        # Business category (autocomplete - type and select)
        category = business.get("category", "")
        if category:
            await self.type_slowly(page, '#GeneralInfoStep_BussinessCategory_Input', category, field_name="Κατηγορία")
            await asyncio.sleep(1.5)
            await self.safe_click(page, '.ui-autocomplete .ui-menu-item:first-child, .ui-autocomplete li:first-child, .ui-menu-item-wrapper:first-child', timeout=3000)

        # Address
        await self.safe_fill(page, '#GeneralInfoStep_Address', business.get("address", ""), field_name="Διεύθυνση")

        # Region / Prefecture (autocomplete)
        region = business.get("region", "") or business.get("city", "")
        if region:
            await self.type_slowly(page, '#GeneralInfoStep_Region', region, field_name="Περιοχή")
            await asyncio.sleep(1)
            await self.safe_click(page, '.ui-autocomplete .ui-menu-item:first-child, .ui-autocomplete li:first-child', timeout=2000)

        # Zip code
        await self.safe_fill(page, '#GeneralInfoStep_ZipCode', business.get("postal_code", ""), field_name="Τ.Κ.")

        # Email (required - CRITICAL for verification)
        email_filled = await self.safe_fill(page, '#GeneralInfoStep_Email', business.get("email", ""), field_name="Email")
        if not email_filled and business.get("email"):
            await self.emit("fill", "running", "ΠΡΟΣΟΧΗ: Το πεδίο email δεν βρέθηκε!")

        # Website
        await self.safe_fill(page, '#GeneralInfoStep_Website', business.get("website", ""), field_name="Website")

        # Phone (required)
        await self.safe_fill(page, '#GeneralInfoStep_Phone', business.get("phone", ""), field_name="Τηλέφωνο")

        # Second phone / mobile
        await self.safe_fill(page, '#GeneralInfoStep_SecondPhone', business.get("mobile", ""), field_name="Κινητό")

        # Company description
        desc_gr = business.get("description_gr", "")
        if desc_gr:
            await self.safe_fill(page, '#GeneralInfoStep_CompanyDescription', desc_gr, field_name="Περιγραφή")

        # Product/service description
        desc_en = business.get("description_en", "")
        if desc_en:
            await self.safe_fill(page, '#GeneralInfoStep_ProductDescription', desc_en, field_name="Περιγραφή Προϊόντος")

        # Contact person
        await self.safe_fill(page, '#GeneralInfoStep_ContactPersonName', business.get("contact_person", ""), field_name="Υπεύθυνος")

        # Contact phone
        await self.safe_fill(page, '#GeneralInfoStep_ContactPersonPhone', business.get("phone", ""), field_name="Τηλ. Υπεύθυνου")

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        # Try auto-solving CAPTCHA before clicking next
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "Vrisko.gr: Δεν λύθηκε αυτόματα το CAPTCHA. Λύστε το χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        url_before = page.url

        # Click submit/next button (step 1)
        clicked = await self.safe_click(page, '#buttonNext')
        if not clicked:
            return AutomationResult(
                success=False,
                directory_id=self.directory_id,
                message=f"Vrisko.gr: Δεν βρέθηκε το κουμπί 'Επόμενο'. {self.field_summary()}",
            )

        await asyncio.sleep(3)

        # Check for step 1 errors before proceeding
        errors = await self.check_page_errors(page)
        if errors:
            return AutomationResult(
                success=False,
                directory_id=self.directory_id,
                message=f"Vrisko.gr: Σφάλματα στο βήμα 1: {'; '.join(errors[:3])}. {self.field_summary()}",
            )

        # The next step might be CAPTCHA/terms acceptance
        try:
            terms_checkbox = page.locator('#CaptchaStep_CaptchaAcceptTermsAgreement')
            if await terms_checkbox.count() > 0:
                await page.evaluate("document.getElementById('CaptchaStep_CaptchaAcceptTermsAgreement').value = 'True'")
        except Exception:
            pass

        # Check if there's another CAPTCHA on the next step
        solved2 = await self.try_solve_captcha(page)
        if not solved2:
            await self.pause_for_human(
                "Vrisko.gr: Αποδεχτείτε τους όρους, λύστε το CAPTCHA και πατήστε 'Συνέχεια'."
            )

        # Click next again for final submission
        await self.safe_click(page, '#buttonNext')

        await asyncio.sleep(5)

        # Verify final submission
        result = await self.verify_submission(
            page, url_before,
            success_indicators=[
                "Ευχαριστούμε", "ευχαριστούμε", "επιτυχ", "ολοκληρώθηκε",
                ".success", ".alert-success", ".thank-you", ".completion",
            ],
            error_indicators=[
                ".field-validation-error", ".validation-summary-errors",
                ".alert-danger", "υποχρεωτικό", "απαιτείται", "λάθος",
            ],
        )

        return AutomationResult(
            success=result["success"],
            directory_id=self.directory_id,
            message=f"Vrisko.gr: {result['message']} {self.field_summary()}",
            url=page.url if result["success"] else "",
        )
