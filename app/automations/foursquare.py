from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class FoursquareAutomation(BaseAutomation):
    directory_id = "foursquare"
    directory_name = "Foursquare"
    registration_url = "https://foursquare.com/add-place"
    search_url = "https://foursquare.com/explore?near={city}&q={name}"

    async def fill_form(self, page: Page, business: dict):
        # Foursquare redirects to login
        await asyncio.sleep(2)
        await page.wait_for_load_state('networkidle', timeout=10000)

        current_url = page.url
        if 'login' in current_url or 'auth' in current_url:
            # Fill email/username on login page
            email = business.get("email", "")
            await self.safe_fill(page, 'input#username, input[name="username"], input[type="text"]', email)

            await self.pause_for_human(
                "Foursquare: Συνδεθείτε με τον λογαριασμό σας. Πατήστε 'Συνέχεια' αφού μπείτε."
            )
            await asyncio.sleep(2)
            await page.wait_for_load_state('networkidle', timeout=10000)

        # Now on add-place form
        name = business.get("name_en", "") or business.get("name", "")
        await self.safe_fill(page, 'input[name="name"], input[aria-label="Place Name"], input[placeholder*="name" i]', name)

        # Category (autocomplete)
        category = business.get("category_en", "") or business.get("category", "")
        if category:
            cat_selector = 'input[name="category"], input[aria-label="Category"], [role="combobox"]'
            await self.type_slowly(page, cat_selector, category)
            await asyncio.sleep(1)
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")

        # Address
        await self.safe_fill(page, 'input[name="address"], input[aria-label="Address"]', business.get("address", ""))

        # City
        city = business.get("city_en", "") or business.get("city", "")
        await self.safe_fill(page, 'input[name="locality"], input[name="city"], input[aria-label="Locality"]', city)

        # Region
        region = business.get("region", "")
        await self.safe_fill(page, 'input[name="region"], input[name="state"], input[aria-label="Region"]', region)

        # Postal code
        await self.safe_fill(page, 'input[name="postalCode"], input[name="zip"], input[aria-label="Postal Code"]', business.get("postal_code", ""))

        # Country
        await self.safe_fill(page, 'input[name="country"], input[aria-label="Country"]', "Greece")

        # Phone
        await self.safe_fill(page, 'input[name="phone"], input[aria-label="Phone"]', business.get("phone", ""))

        # Website
        await self.safe_fill(page, 'input[name="website"], input[name="url"], input[aria-label="Website"]', business.get("website", ""))

        # Email
        await self.safe_fill(page, 'input[name="email"], input[aria-label="Email"]', business.get("email", ""))

        # Social
        await self.safe_fill(page, 'input[name="facebook"], input[name="facebookId"]', business.get("facebook", ""))
        await self.safe_fill(page, 'input[name="instagram"], input[aria-label="Instagram"]', business.get("instagram", ""))

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        await self.pause_for_human(
            "Foursquare: Ελέγξτε τα στοιχεία, τοποθετήστε τον pin στον χάρτη, "
            "και πατήστε 'Συνέχεια'."
        )

        await self.safe_click(page, 'button[type="submit"], button:has-text("Save"), button:has-text("Add"), button:has-text("Submit")')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Foursquare: Τοποθεσία προστέθηκε.",
            url="https://foursquare.com",
        )
