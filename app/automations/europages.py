from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class EuropagesAutomation(BaseAutomation):
    directory_id = "europages"
    directory_name = "Europages"
    registration_url = "https://www.europages.co.uk/en/supplier-registration"

    async def fill_form(self, page: Page, business: dict):
        # Europages redirects to Visable SSO for registration
        await asyncio.sleep(3)
        await page.wait_for_load_state('networkidle', timeout=15000)

        # Step 1: Fill email on auth page
        email = business.get("email", "")
        if email:
            await self.safe_fill(page, 'input[name="email"], input[type="email"], #email', email)

        # Fill name fields if visible
        name = business.get("contact_person", "") or business.get("name_en", "") or business.get("name", "")
        parts = name.split(" ", 1) if name else ["", ""]
        await self.safe_fill(page, 'input[name="firstName"], input[name="first_name"]', parts[0])
        await self.safe_fill(page, 'input[name="lastName"], input[name="last_name"]', parts[1] if len(parts) > 1 else "")

        # Human must complete registration (password, email verification code)
        await self.pause_for_human(
            "Europages: Συμπληρώστε password, πατήστε register, εισάγετε τον κωδικό από το email. "
            "Πατήστε 'Συνέχεια' όταν μπείτε στο company profile."
        )

        # After login, fill company profile
        await asyncio.sleep(2)
        await page.wait_for_load_state('networkidle', timeout=10000)

        company_name = business.get("name_en", "") or business.get("name", "")
        await self.safe_fill(page, 'input[name="companyName"], input[name="company_name"]', company_name)
        await self.safe_fill(page, 'input[name="street"], input[name="streetAndNumber"]', business.get("address", ""))
        await self.safe_fill(page, 'input[name="zipCode"], input[name="zip_code"]', business.get("postal_code", ""))
        city = business.get("city_en", "") or business.get("city", "")
        await self.safe_fill(page, 'input[name="city"]', city)
        await self.safe_fill(page, 'input[name="phone"], input[name="phoneNumber"], input[type="tel"]', business.get("phone", ""))
        await self.safe_fill(page, 'input[name="website"], input[name="url"]', business.get("website", ""))

        # VAT / Tax ID
        tax_id = business.get("tax_id", "")
        if tax_id:
            await self.safe_fill(page, 'input[name="vatNumber"], input[name="vat"]', tax_id)

        desc = business.get("description_en", "") or business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, 'textarea[name="description"], textarea[name="companyDescription"]', desc[:1500])

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        await self.pause_for_human(
            "Europages: Ελέγξτε το company profile και αποθηκεύστε. Πατήστε 'Συνέχεια' όταν τελειώσετε."
        )

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Europages: Προφίλ δημιουργήθηκε/ενημερώθηκε.",
            url="https://www.europages.co.uk",
        )
