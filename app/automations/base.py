import asyncio
from playwright.async_api import async_playwright, Page, Browser
from typing import Optional, Callable
from dataclasses import dataclass, field


@dataclass
class AutomationResult:
    success: bool
    directory_id: str
    message: str
    url: str = ""


@dataclass
class ProgressEvent:
    directory_id: str
    step: str
    status: str  # "running", "waiting_human", "success", "error"
    message: str


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

    async def run(self, business: dict) -> AutomationResult:
        """Run the full automation flow for a business."""
        try:
            await self.emit("start", "running", f"Starting {self.directory_name}...")

            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,
                    slow_mo=300,
                )
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 900},
                    locale="el-GR",
                )
                page = await context.new_page()

                await self.emit("navigate", "running", f"Opening {self.registration_url}...")
                await page.goto(self.registration_url, wait_until="domcontentloaded", timeout=30000)

                await self.emit("fill", "running", "Filling form fields...")
                await self.fill_form(page, business)

                await self.emit("review", "waiting_human",
                    "Form filled! Review the data, solve any CAPTCHA, then click Continue in the dashboard.")
                self._human_event.clear()
                await self._human_event.wait()

                await self.emit("submit", "running", "Submitting...")
                result = await self.submit(page, business)

                await asyncio.sleep(3)
                await browser.close()

                await self.emit("done", "success", result.message)
                return result

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            await self.emit("error", "error", error_msg)
            return AutomationResult(
                success=False,
                directory_id=self.directory_id,
                message=error_msg,
            )

    async def fill_form(self, page: Page, business: dict):
        """Override in subclass to fill directory-specific form."""
        raise NotImplementedError

    async def submit(self, page: Page, business: dict) -> AutomationResult:
        """Override in subclass to handle submission."""
        return AutomationResult(
            success=True,
            directory_id=self.directory_id,
            message="Submitted successfully (manual verification may be needed)",
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
