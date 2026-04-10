from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class BrownbookAutomation(BaseAutomation):
    directory_id = "brownbook"
    directory_name = "Brownbook.net"
    registration_url = "https://www.brownbook.net/add-business/"
    search_url = "https://www.brownbook.net/businesses/{name}+{city}/"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Close cookie banner
        await self.safe_click(page, '.cookie-accept, #accept-cookies, button:has-text("Accept")', timeout=3000)

        # Business name
        await self.safe_fill(page, 'input[name="name"]', business.get("name", ""))

        # Category (combobox dropdown)
        category = business.get("category_en", "") or business.get("category", "")
        if category:
            await self.safe_click(page, 'button[role="combobox"]', timeout=3000)
            await asyncio.sleep(0.5)
            # Type to filter in the dropdown
            await page.keyboard.type(category)
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
            await asyncio.sleep(0.5)

        # Address (textarea)
        await self.safe_fill(page, 'textarea[name="address"]', business.get("address", ""))

        # City
        await self.safe_fill(page, 'input[name="city"]', business.get("city", ""))

        # Zip code
        await self.safe_fill(page, 'input[name="zip_code"]', business.get("postal_code", ""))

        # Phone
        await self.safe_fill(page, 'input[name="phone"]', business.get("phone", ""))

        # Mobile
        await self.safe_fill(page, 'input[name="mobile"]', business.get("mobile", ""))

        # Email
        await self.safe_fill(page, 'input[name="email"]', business.get("email", ""))

        # Website
        await self.safe_fill(page, 'input[name="website"]', business.get("website", ""))

        # Facebook
        facebook = business.get("facebook", "")
        if facebook:
            await self.safe_fill(page, 'input[name="facebook"]', facebook)

        # Instagram
        instagram = business.get("instagram", "")
        if instagram:
            await self.safe_fill(page, 'input[name="instagram"]', instagram)

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "Brownbook: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        await self.safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Brownbook.net: Η επιχείρηση καταχωρήθηκε.",
            url="https://www.brownbook.net",
        )
