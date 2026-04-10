from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class CyboAutomation(BaseAutomation):
    directory_id = "cybo"
    directory_name = "Cybo"
    registration_url = "https://www.cybo.com/add-business"
    search_url = "https://www.cybo.com/search/?q={name}+{city}&loc=Greece"

    async def fill_form(self, page: Page, business: dict):
        # Cybo redirects to login page first
        await asyncio.sleep(2)
        await page.wait_for_load_state('networkidle', timeout=10000)

        # Check if we're on login page
        current_url = page.url
        if 'log-in' in current_url or 'login' in current_url:
            await self.pause_for_human(
                "Cybo: Χρειάζεται login. Συνδεθείτε ή δημιουργήστε λογαριασμό, "
                "μετά πατήστε 'Συνέχεια'."
            )
            await asyncio.sleep(2)
            await page.wait_for_load_state('networkidle', timeout=10000)

        # Now on add-business form - fill fields
        name = business.get("name_en", "") or business.get("name", "")
        await self.safe_fill(page, 'input[name="name"], input[name="business_name"], input#id_name', name)
        await self.safe_fill(page, 'input[name="phone"], input#id_phone, input[type="tel"]', business.get("phone", ""))
        await self.safe_fill(page, 'input[name="email"], input#id_email', business.get("email", ""))
        await self.safe_fill(page, 'input[name="address"], input#id_address', business.get("address", ""))

        city = business.get("city_en", "") or business.get("city", "")
        await self.safe_fill(page, 'input[name="city"], input#id_city', city)
        await self.safe_fill(page, 'input[name="zip"], input[name="postal_code"], input#id_zip', business.get("postal_code", ""))
        await self.safe_fill(page, 'input[name="website"], input[name="url"], input#id_website', business.get("website", ""))

        desc = business.get("description_en", "") or business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, 'textarea[name="description"], textarea#id_description', desc)

        # Country - select Greece
        await self.safe_select(page, 'select[name="country"], select#id_country', "GR")

        # Category
        category = business.get("category_en", "") or business.get("category", "")
        if category:
            await self.type_slowly(page, 'input[name="category"], input#id_category', category)
            await asyncio.sleep(1)
            await self.safe_click(page, '.ui-autocomplete li:first-child, .autocomplete-suggestion:first-child', timeout=2000)

        # Social media
        await self.safe_fill(page, 'input[name="facebook"], input#id_facebook', business.get("facebook", ""))
        await self.safe_fill(page, 'input[name="instagram"], input#id_instagram', business.get("instagram", ""))

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        await self.pause_for_human(
            "Cybo: Ελέγξτε τα στοιχεία και πατήστε 'Συνέχεια' για υποβολή."
        )

        await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Cybo: Επιχείρηση υποβλήθηκε.",
            url="https://www.cybo.com",
        )
