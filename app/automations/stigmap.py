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
        await self.safe_fill(page, 'input[name="name"], input[name="business_name"], #name, #business_name', business.get("name", ""))

        # Category
        category = business.get("category", "")
        if category:
            await self.safe_fill(page, 'input[name="category"], #category, select[name="category"]', category)

        # Phone
        await self.safe_fill(page, 'input[name="phone"], #phone', business.get("phone", ""))

        # Email
        await self.safe_fill(page, 'input[name="email"], #email', business.get("email", ""))

        # Address
        await self.safe_fill(page, 'input[name="address"], #address', business.get("address", ""))

        # City
        await self.safe_fill(page, 'input[name="city"], #city', business.get("city", ""))

        # Website
        await self.safe_fill(page, 'input[name="website"], #website', business.get("website", ""))

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "StigMap.gr: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="StigMap.gr: Φόρμα υποβλήθηκε.",
            url="https://www.stigmap.gr",
        )
