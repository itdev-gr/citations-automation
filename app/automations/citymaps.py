from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class CityMapsAutomation(BaseAutomation):
    directory_id = "citymaps"
    directory_name = "CityMaps.gr"
    registration_url = "https://citymaps.gr/"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Close cookie banner
        await self.safe_click(page, '.cookie-accept, #accept-cookies, button:has-text("Αποδοχή"), button:has-text("Accept")', timeout=3000)

        # Look for add business / registration link
        await self.safe_click(page, 'a:has-text("Καταχώρηση"), a:has-text("Προσθήκη"), a:has-text("Εγγραφή"), a[href*="add"], a[href*="register"], a[href*="submit"]', timeout=5000)
        await asyncio.sleep(2)

        # Business name
        await self.safe_fill(page, 'input[name="name"], input[name="business_name"], input[name="title"], #name, #business_name, #title', business.get("name", ""))

        # Category
        category = business.get("category", "")
        if category:
            await self.safe_fill(page, 'input[name="category"], #category, select[name="category"]', category)

        # Phone
        await self.safe_fill(page, 'input[name="phone"], #phone, input[name="tel"]', business.get("phone", ""))

        # Email
        await self.safe_fill(page, 'input[name="email"], #email', business.get("email", ""))

        # Address
        await self.safe_fill(page, 'input[name="address"], #address', business.get("address", ""))

        # City
        await self.safe_fill(page, 'input[name="city"], #city', business.get("city", ""))

        # Website
        await self.safe_fill(page, 'input[name="website"], input[name="url"], #website', business.get("website", ""))

        # Description
        desc = business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, 'textarea[name="description"], textarea#description, textarea[name="content"]', desc)

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "CityMaps.gr: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="CityMaps.gr: Φόρμα υποβλήθηκε.",
            url="https://citymaps.gr",
        )
