"""
JARVIS Browser Controller — Playwright-based async browser automation.
Supports: navigate, click, fill, screenshot, extract, eval_js.
Phase 4: headless Chromium. Phase 5: LiveView integration.
"""
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from loguru import logger
from typing import Optional
import base64, asyncio

_playwright = None
_browser: Optional[Browser] = None
_context: Optional[BrowserContext] = None


async def get_browser() -> Browser:
    global _playwright, _browser
    if _browser is None or not _browser.is_connected():
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        )
        logger.info("Browser launched")
    return _browser


async def get_context() -> BrowserContext:
    global _context
    browser = await get_browser()
    if _context is None:
        _context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )
    return _context


async def close_browser():
    global _browser, _context, _playwright
    if _context:
        await _context.close()
        _context = None
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None


class BrowserSession:
    """Managed browser session with auto-cleanup."""
    def __init__(self):
        self.page: Optional[Page] = None

    async def __aenter__(self):
        context = await get_context()
        self.page = await context.new_page()
        return self

    async def __aexit__(self, *args):
        if self.page:
            await self.page.close()

    async def navigate(self, url: str, wait_for: str = "load") -> dict:
        await self.page.goto(url, wait_until=wait_for, timeout=30000)
        return {"url": self.page.url, "title": await self.page.title()}

    async def screenshot(self, full_page: bool = False) -> str:
        """Take screenshot, return base64 PNG."""
        img = await self.page.screenshot(full_page=full_page, type="png")
        return base64.b64encode(img).decode()

    async def extract_text(self, selector: str = "body") -> str:
        """Extract visible text from selector."""
        try:
            return await self.page.inner_text(selector)
        except Exception:
            return await self.page.evaluate("document.body.innerText")

    async def extract_links(self) -> list:
        return await self.page.evaluate("""() =>
            Array.from(document.links).map(a => ({text: a.innerText.trim(), href: a.href}))
            .filter(l => l.href && l.text).slice(0, 50)
        """)

    async def click(self, selector: str) -> dict:
        await self.page.click(selector, timeout=10000)
        await self.page.wait_for_load_state("networkidle", timeout=10000)
        return {"clicked": selector, "url": self.page.url}

    async def fill(self, selector: str, value: str) -> dict:
        await self.page.fill(selector, value)
        return {"filled": selector}

    async def eval_js(self, script: str) -> any:
        return await self.page.evaluate(script)

    async def wait_for_selector(self, selector: str, timeout: int = 10000) -> bool:
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False
