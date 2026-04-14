from playwright.async_api import Page
from .base import BaseAutomation, AutomationResult


# Prefecture mapping: Greek region name -> xo.gr value
PREFECTURE_MAP = {
    "αττική": "E1", "αττικής": "E1", "αθήνα": "E1", "athens": "E1",
    "θεσσαλονίκη": "E3", "θεσσαλονίκης": "E3", "thessaloniki": "E3",
    "αχαΐα": "E6", "αχαΐας": "E6", "πάτρα": "E6",
    "ηράκλειο": "E7", "ηρακλείου": "E7", "κρήτη": "E7",
    "λάρισα": "E8", "λάρισας": "E8",
    "αιτωλοακαρνανία": "E9", "αιτωλοακαρνανίας": "E9",
    "εύβοια": "E10", "ευβοίας": "E10",
    "μαγνησία": "E11", "μαγνησίας": "E11",
    "σέρρες": "E12", "σερρών": "E12",
    "ηλεία": "E13", "ηλείας": "E13",
    "δωδεκάνησα": "E14", "δωδεκανήσου": "E14", "ρόδος": "E14",
    "φθιώτιδα": "E15", "φθιώτιδας": "E15",
    "μεσσηνία": "E16", "μεσσηνίας": "E16",
    "ιωάννινα": "E17", "ιωαννίνων": "E17",
    "κοζάνη": "E18", "κοζάνης": "E18",
    "κορινθία": "E19", "κορινθίας": "E19",
    "χανιά": "E21", "χανίων": "E21",
    "έβρος": "E22", "έβρου": "E22",
    "πέλλα": "E23", "πέλλας": "E23",
    "καβάλα": "E24", "καβάλας": "E24",
    "ημαθία": "E25", "ημαθίας": "E25",
    "τρίκαλα": "E26", "τρικάλων": "E26",
    "βοιωτία": "E27", "βοιωτίας": "E27",
    "πιερία": "E28", "πιερίας": "E28",
    "καρδίτσα": "E29", "καρδίτσας": "E29",
    "κυκλάδες": "E30", "κυκλάδων": "E30",
    "κέρκυρα": "E31", "κερκύρας": "E31",
    "ροδόπη": "E32", "ροδόπης": "E32",
    "λέσβος": "E33", "λέσβου": "E33",
    "αργολίδα": "E34", "αργολίδας": "E34",
    "χαλκιδική": "E35", "χαλκιδικής": "E35",
    "δράμα": "E36", "δράμας": "E36",
    "αρκαδία": "E37", "αρκαδίας": "E37",
    "ξάνθη": "E38", "ξάνθης": "E38",
    "λακωνία": "E39", "λακωνίας": "E39",
    "κιλκίς": "E40",
    "ρέθυμνο": "E41", "ρεθύμνης": "E41",
    "άρτα": "E42", "άρτας": "E42",
    "λασίθι": "E43", "λασιθίου": "E43",
    "πρέβεζα": "E44", "πρέβεζας": "E44",
    "καστοριά": "E45", "καστοριάς": "E45",
    "φλώρινα": "E45", "φλώρινας": "E45",
    "χίος": "E47", "χίου": "E47",
    "φωκίδα": "E48", "φωκίδας": "E48",
    "θεσπρωτία": "E49", "θεσπρωτίας": "E49",
    "σάμος": "E50", "σάμου": "E50",
    "κεφαλονιά": "E51", "κεφαλληνίας": "E51",
    "ζάκυνθος": "E52", "ζακύνθου": "E52",
    "γρεβενά": "E53", "γρεβενών": "E53",
    "ευρυτανία": "E54", "ευρυτανίας": "E54",
    "λευκάδα": "E55", "λευκάδας": "E55",
}


def get_prefecture_value(region: str) -> str:
    """Map a Greek region/city name to xo.gr prefecture value."""
    if not region:
        return ""
    lower = region.lower().strip()
    # Try exact match
    if lower in PREFECTURE_MAP:
        return PREFECTURE_MAP[lower]
    # Try partial match
    for key, val in PREFECTURE_MAP.items():
        if key in lower or lower in key:
            return val
    return ""


class XoGrAutomation(BaseAutomation):
    directory_id = "xo_gr"
    directory_name = "Χρυσός Οδηγός (xo.gr)"
    registration_url = "https://www.xo.gr/dorean-katachorisi/"

    async def fill_form(self, page: Page, business: dict):
        import asyncio

        # Close cookie banner if present
        await self.safe_click(page, '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll, .cookiescript_accept', timeout=3000)

        # Business name (required)
        await self.safe_fill(page, 'input#business_name', business.get("name", ""), field_name="Επωνυμία")

        # Phone (required)
        await self.safe_fill(page, 'input#main_phone', business.get("phone", ""), field_name="Τηλέφωνο")

        # Mobile
        await self.safe_fill(page, 'input#BusinessMobile', business.get("mobile", ""), field_name="Κινητό")

        # Address
        await self.safe_fill(page, 'input#BusinessAddress', business.get("address", ""), field_name="Διεύθυνση")

        # Postal code
        await self.safe_fill(page, 'input#BusinessPostCode', business.get("postal_code", ""), field_name="Τ.Κ.")

        # Prefecture (select dropdown)
        prefecture = get_prefecture_value(business.get("region", "") or business.get("city", ""))
        if prefecture:
            await self.safe_select(page, 'select#BusinessPrefectureId', prefecture, field_name="Νομός")
            await asyncio.sleep(0.5)

        # City (autocomplete - type slowly)
        await self.type_slowly(page, 'input#BusinessCity', business.get("city", ""), field_name="Πόλη")
        await asyncio.sleep(1)
        await self.safe_click(page, '.ui-autocomplete .ui-menu-item:first-child, .ui-autocomplete li:first-child', timeout=2000)

        # Business activity / category (autocomplete)
        category = business.get("category", "")
        if category:
            await self.type_slowly(page, 'input#BusinessActivity', category, field_name="Κατηγορία")
            await asyncio.sleep(1)
            await self.safe_click(page, '.ui-autocomplete .ui-menu-item:first-child, .ui-autocomplete li:first-child', timeout=2000)

        # Specialization
        desc = business.get("description_gr", "")
        if desc:
            await self.safe_fill(page, 'input#BusinessSpecialization', desc[:200], field_name="Εξειδίκευση")

        # Contact person
        await self.safe_fill(page, 'input#contactPersonName', business.get("contact_person", ""), field_name="Υπεύθυνος")

        # Contact position
        await self.safe_fill(page, 'input#contactPersonPosition', 'Ιδιοκτήτης', field_name="Θέση")

        # Contact phone
        await self.safe_fill(page, 'input#contactPersonContactPhone', business.get("phone", ""), field_name="Τηλ. Επικοινωνίας")

        # Contact email (CRITICAL - needed for verification)
        email_filled = await self.safe_fill(page, 'input#contactPersonContactEmail', business.get("email", ""), field_name="Email")
        if not email_filled and business.get("email"):
            await self.emit("fill", "running", "ΠΡΟΣΟΧΗ: Το πεδίο email δεν βρέθηκε! Δεν θα έρθει verification email.")

        # Website
        await self.safe_fill(page, 'input#contactPersonContactWebsite', business.get("website", ""), field_name="Website")

        # Newsletter checkbox (optional)
        await self.safe_click(page, 'input#cbAcceptedInfo', timeout=2000)

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        import asyncio

        # Try auto-solving CAPTCHA first
        solved = await self.try_solve_captcha(page)
        if not solved:
            await self.pause_for_human(
                "Χρυσός Οδηγός: Δεν λύθηκε αυτόματα το CAPTCHA. Λύστε το χειροκίνητα και πατήστε 'Συνέχεια'."
            )

        url_before = page.url

        # Click submit button
        clicked = await self.safe_click(page, 'button[type="submit"], input[type="submit"], .freelisting-submit-btn, #submitBtn')
        if not clicked:
            return AutomationResult(
                success=False,
                directory_id=self.directory_id,
                message=f"XO.gr: Δεν βρέθηκε το κουμπί υποβολής. {self.field_summary()}",
            )

        await asyncio.sleep(5)

        # Verify submission
        result = await self.verify_submission(
            page, url_before,
            success_indicators=[
                "Ευχαριστούμε", "ευχαριστούμε", "επιτυχ", "καταχώρηση",
                ".success", ".alert-success", ".thank-you",
            ],
            error_indicators=[
                ".field-validation-error", ".validation-summary-errors",
                ".alert-danger", "υποχρεωτικό", "απαιτείται",
            ],
        )

        return AutomationResult(
            success=result["success"],
            directory_id=self.directory_id,
            message=f"XO.gr: {result['message']} {self.field_summary()}",
            url=page.url if result["success"] else "",
        )
