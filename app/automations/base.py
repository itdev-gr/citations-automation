import asyncio
import os
from playwright.async_api import async_playwright, Page, Browser
from playwright_stealth import Stealth
from typing import Optional, Callable
from dataclasses import dataclass, field


@dataclass
class AutomationResult:
    success: bool
    directory_id: str
    message: str
    url: str = ""
    screenshot: str = ""


@dataclass
class ProgressEvent:
    directory_id: str
    step: str
    status: str  # "running", "waiting_human", "success", "error"
    message: str


async def solve_recaptcha_v2(page: Page, sitekey: str = None) -> bool:
    """Solve reCAPTCHA v2 using 2Captcha service."""
    api_key = os.environ.get("TWOCAPTCHA_API_KEY", "")
    if not api_key:
        return False

    try:
        from twocaptcha import TwoCaptcha
        solver = TwoCaptcha(api_key)

        # Find sitekey from page if not provided
        if not sitekey:
            sitekey = await page.evaluate("""
                () => {
                    const el = document.querySelector('.g-recaptcha, [data-sitekey]');
                    return el ? el.getAttribute('data-sitekey') : null;
                }
            """)

        if not sitekey:
            return False

        url = page.url

        # Solve in background thread (blocking call)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: solver.recaptcha(sitekey=sitekey, url=url)
        )

        token = result.get('code', '')
        if not token:
            return False

        # Inject the token into the page
        await page.evaluate(f"""
            () => {{
                const textarea = document.getElementById('g-recaptcha-response');
                if (textarea) {{
                    textarea.style.display = 'block';
                    textarea.value = '{token}';
                }}
                // Also try callback
                if (typeof ___grecaptcha_cfg !== 'undefined') {{
                    Object.entries(___grecaptcha_cfg.clients).forEach(([k, v]) => {{
                        const callback = v?.['P']?.['P']?.callback || v?.callback;
                        if (typeof callback === 'function') callback('{token}');
                    }});
                }}
            }}
        """)
        return True

    except Exception as e:
        print(f"2Captcha error: {e}")
        return False


class BaseAutomation:
    directory_id: str = ""
    directory_name: str = ""
    registration_url: str = ""

    def __init__(self, on_progress: Optional[Callable] = None):
        self.on_progress = on_progress
        self._human_event = asyncio.Event()

    async def emit(self, step: str, status: str, message: str):
        if self.on_progress:
            event = ProgressEvent(
                directory_id=self.directory_id,
                step=step,
                status=status,
                message=message,
            )
            await self.on_progress(event)

    async def pause_for_human(self, reason: str):
        """Pause automation and wait for human to complete an action (CAPTCHA, verification, etc)."""
        await self.emit("human_action", "waiting_human", reason)
        self._human_event.clear()
        await self._human_event.wait()
        await self.emit("human_action", "running", "Continuing after human action...")

    def resume_after_human(self):
        """Called when user signals they've completed the manual action."""
        self._human_event.set()

    async def try_solve_captcha(self, page: Page) -> bool:
        """Try to solve reCAPTCHA on the page. Returns True if solved."""
        # Check if there's a reCAPTCHA on the page
        has_captcha = await page.evaluate("""
            () => {
                return !!(
                    document.querySelector('.g-recaptcha') ||
                    document.querySelector('[data-sitekey]') ||
                    document.querySelector('iframe[src*="recaptcha"]')
                );
            }
        """)

        if not has_captcha:
            return True  # No CAPTCHA = success

        await self.emit("captcha", "running", "Λύνω CAPTCHA αυτόματα...")

        solved = await solve_recaptcha_v2(page)
        if solved:
            await self.emit("captcha", "running", "CAPTCHA λύθηκε!")
            return True
        else:
            # Fall back to human
            await self.emit("captcha", "waiting_human",
                "Δεν μπόρεσα να λύσω το CAPTCHA αυτόματα. Λύστε το χειροκίνητα και πατήστε 'Συνέχεια'.")
            return False

    # Search URL template for duplicate checking — override in subclass
    # Use {name} and {city} placeholders, e.g. "https://example.com/search?q={name}+{city}"
    search_url: str = ""

    async def check_duplicate(self, page: Page, business: dict) -> Optional[str]:
        """Check if business already exists on this directory.
        Returns the listing URL if found, None otherwise.
        Override in subclass for directory-specific search logic."""
        if not self.search_url:
            return None

        name = business.get("name_en") or business.get("name", "")
        city = business.get("city_en") or business.get("city", "")

        from urllib.parse import quote_plus
        url = self.search_url.replace("{name}", quote_plus(name)).replace("{city}", quote_plus(city))

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2)

            # Look for the business name in search results
            found = await page.evaluate(f"""
                () => {{
                    const name = "{name.replace('"', '\\"').lower()}";
                    const links = document.querySelectorAll('a');
                    for (const link of links) {{
                        if (link.textContent.toLowerCase().includes(name) && link.href) {{
                            return link.href;
                        }}
                    }}
                    return null;
                }}
            """)
            return found
        except Exception:
            return None

    async def run(self, business: dict, proxy: str = None) -> AutomationResult:
        """Run the full automation flow for a business."""
        try:
            await self.emit("start", "running", f"Εκκίνηση {self.directory_name}...")

            launch_args = [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]
            launch_opts = {"headless": True, "args": launch_args}
            if proxy:
                launch_opts["proxy"] = {"server": proxy}

            async with async_playwright() as p:
                browser = await p.chromium.launch(**launch_opts)
                context = await browser.new_context(
                    viewport={"width": 1366, "height": 768},
                    locale="el-GR",
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                )
                page = await context.new_page()
                stealth = Stealth()
                await stealth.apply_stealth_async(page)

                # --- Duplicate check ---
                await self.emit("check", "running", "Έλεγχος αν υπάρχει ήδη...")
                existing_url = await self.check_duplicate(page, business)
                if existing_url:
                    await browser.close()
                    await self.emit("done", "already_listed", f"Η επιχείρηση υπάρχει ήδη: {existing_url}")
                    return AutomationResult(
                        success=True,
                        directory_id=self.directory_id,
                        message=f"Υπάρχει ήδη στον κατάλογο.",
                        url=existing_url,
                    )

                await self.emit("navigate", "running", f"Άνοιγμα {self.registration_url}...")
                await page.goto(self.registration_url, wait_until="domcontentloaded", timeout=30000)

                await self.emit("fill", "running", "Συμπλήρωση πεδίων...")
                await self.fill_form(page, business)

                await self.emit("submit", "running", "Υποβολή...")
                result = await self.submit(page, business)

                # --- Screenshot proof ---
                screenshot_path = await self._take_screenshot(page, business)
                if screenshot_path:
                    result.screenshot = screenshot_path

                await asyncio.sleep(3)
                await browser.close()

                await self.emit("done", "success", result.message)
                return result

        except Exception as e:
            error_msg = f"Σφάλμα: {str(e)}"
            await self.emit("error", "error", error_msg)
            return AutomationResult(
                success=False,
                directory_id=self.directory_id,
                message=error_msg,
            )

    async def _take_screenshot(self, page: Page, business: dict) -> str:
        """Take a screenshot as proof of submission."""
        try:
            os.makedirs("/opt/citations/screenshots", exist_ok=True)
            biz_name = (business.get("name", "unknown")).replace(" ", "_").replace("/", "_")[:30]
            filename = f"{self.directory_id}_{biz_name}_{int(asyncio.get_event_loop().time())}.png"
            path = f"/opt/citations/screenshots/{filename}"
            await page.screenshot(path=path, full_page=True)
            return filename
        except Exception:
            return ""

    async def fill_form(self, page: Page, business: dict):
        """Override in subclass to fill directory-specific form."""
        raise NotImplementedError

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        """Override in subclass to handle submission."""
        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Υποβλήθηκε επιτυχώς",
        )

    # Helper methods for common form operations
    async def safe_fill(self, page: Page, selector: str, value: str, timeout: int = 5000):
        """Fill a field if it exists, skip if not found."""
        if not value:
            return
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            await page.fill(selector, value)
        except Exception:
            pass

    async def safe_click(self, page: Page, selector: str, timeout: int = 5000):
        """Click an element if it exists."""
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            await page.click(selector)
        except Exception:
            pass

    async def safe_select(self, page: Page, selector: str, value: str, timeout: int = 5000):
        """Select an option if the select exists."""
        if not value:
            return
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            await page.select_option(selector, value)
        except Exception:
            pass

    async def type_slowly(self, page: Page, selector: str, value: str, delay: int = 50):
        """Type text character by character (useful for autocomplete fields)."""
        if not value:
            return
        try:
            await page.wait_for_selector(selector, timeout=5000)
            await page.click(selector)
            await page.type(selector, value, delay=delay)
        except Exception:
            pass
