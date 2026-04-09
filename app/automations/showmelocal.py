from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult
import asyncio


class ShowMeLocalAutomation(BaseAutomation):
    directory_id = "showmelocal"
    directory_name = "ShowMeLocal"
    registration_url = "https://www.showmelocal.com/start-submission.aspx"

    async def fill_form(self, page: Page, business: dict):
        await asyncio.sleep(2)

        # Business name
        await self.safe_fill(page, 'input#txtBusinessName, input[name="txtBusinessName"], input[name="BusinessName"]', business.get("name", ""))

        # Phone
        await self.safe_fill(page, 'input#txtPhone, input[name="txtPhone"], input[name="Phone"]', business.get("phone", ""))

        # Address
        await self.safe_fill(page, 'input#txtAddress, input[name="txtAddress"], input[name="Address"]', business.get("address", ""))

        # City
        await self.safe_fill(page, 'input#txtCity, input[name="txtCity"], input[name="City"]', business.get("city", ""))

        # Zip
        await self.safe_fill(page, 'input#txtZip, input[name="txtZip"], input[name="Zip"]', business.get("postal_code", ""))

        # Website
        await self.safe_fill(page, 'input#txtWebsite, input[name="txtWebsite"], input[name="Website"]', business.get("website", ""))

        # Category
        category = business.get("category_en", "") or business.get("category", "")
        if category:
            await self.safe_fill(page, 'input#txtCategory, input[name="txtCategory"], input[name="Category"]', category)
            await asyncio.sleep(1)
            await self.safe_click(page, '.autocomplete-suggestion:first-child, .ui-menu-item:first-child', timeout=2000)

        # Country
        await self.safe_select(page, 'select#ddlCountry, select[name="Country"]', 'Greece')

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "ShowMeLocal: Λύστε το CAPTCHA χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        await self.safe_click(page, 'input#btnSubmit, button[type="submit"], input[type="submit"]')
        await asyncio.sleep(3)

        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="ShowMeLocal: Η επιχείρηση καταχωρήθηκε.",
            url="https://www.showmelocal.com",
        )
