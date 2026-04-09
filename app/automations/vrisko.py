from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class VriskoAutomation(BaseAutomation):
    directory_id = "vrisko"
    directory_name = "Vrisko.gr (11880)"
    registration_url = "https://vriskodigital.vrisko.gr/dorean-kataxorisi/"

    async def fill_form(self, page: Page, business: dict):
        # Company name (required)
        await self.safe_fill(page, '#GeneralInfoStep_CompanyName', business.get("name", ""))

        # Business category (autocomplete - type and select)
        category = business.get("category", "")
        if category:
            await self.type_slowly(page, '#GeneralInfoStep_BussinessCategory_Input', category)
            await asyncio.sleep(1.5)
            # Click first autocomplete suggestion
            await self.safe_click(page, '.ui-autocomplete .ui-menu-item:first-child, .ui-autocomplete li:first-child, .ui-menu-item-wrapper:first-child', timeout=3000)

        # Address
        await self.safe_fill(page, '#GeneralInfoStep_Address', business.get("address", ""))

        # Region / Prefecture (autocomplete)
        region = business.get("region", "") or business.get("city", "")
        if region:
            await self.type_slowly(page, '#GeneralInfoStep_Region', region)
            await asyncio.sleep(1)
            await self.safe_click(page, '.ui-autocomplete .ui-menu-item:first-child, .ui-autocomplete li:first-child', timeout=2000)

        # Zip code
        await self.safe_fill(page, '#GeneralInfoStep_ZipCode', business.get("postal_code", ""))

        # Email (required)
        await self.safe_fill(page, '#GeneralInfoStep_Email', business.get("email", ""))

        # Website
        await self.safe_fill(page, '#GeneralInfoStep_Website', business.get("website", ""))

        # Phone (required)
        await self.safe_fill(page, '#GeneralInfoStep_Phone', business.get("phone", ""))

        # Second phone / mobile
        await self.safe_fill(page, '#GeneralInfoStep_SecondPhone', business.get("mobile", ""))

        # Fax (skip)

        # Company description
        desc_gr = business.get("description_gr", "")
        if desc_gr:
            await self.safe_fill(page, '#GeneralInfoStep_CompanyDescription', desc_gr)

        # Product/service description
        desc_en = business.get("description_en", "")
        if desc_en:
            await self.safe_fill(page, '#GeneralInfoStep_ProductDescription', desc_en)

        # Contact person
        await self.safe_fill(page, '#GeneralInfoStep_ContactPersonName', business.get("contact_person", ""))

        # Contact phone
        await self.safe_fill(page, '#GeneralInfoStep_ContactPersonPhone', business.get("phone", ""))

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        # Pause for human to review and solve CAPTCHA (next step)
        await self.pause_for_human(
            "Vrisko.gr: Η φόρμα συμπληρώθηκε. Ελέγξτε τα στοιχεία και πατήστε 'Συνέχεια' στο dashboard."
        )

        # Click submit/next button
        await self.safe_click(page, '#buttonNext')

        await asyncio.sleep(3)

        # The next step might be CAPTCHA/terms acceptance
        # Try to accept terms if visible
        try:
            terms_checkbox = page.locator('#CaptchaStep_CaptchaAcceptTermsAgreement')
            if await terms_checkbox.count() > 0:
                await page.evaluate("document.getElementById('CaptchaStep_CaptchaAcceptTermsAgreement').value = 'True'")
        except Exception:
            pass

        # Pause again if there's a CAPTCHA step
        await self.pause_for_human(
            "Vrisko.gr: Αποδεχτείτε τους όρους, λύστε το CAPTCHA και πατήστε 'Συνέχεια'."
        )

        # Click next again for final submission
        await self.safe_click(page, '#buttonNext')

        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Vrisko.gr: Φόρμα υποβλήθηκε. Ελέγξτε το email σας.",
            url="https://www.vrisko.gr",
        )
