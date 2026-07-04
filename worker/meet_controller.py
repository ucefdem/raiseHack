"""Google Meet control via Playwright.

Opens Chrome with a persistent, pre-logged-in agent profile, joins the meeting,
disables the camera, keeps the (virtual) microphone on, and detects when the
agent is actually in the call.

Meet's DOM changes often, so selectors are tried in order with fallbacks. If
all selectors fail, a screenshot is saved to help debugging (PRD risk 1).
"""

from __future__ import annotations

import logging
from pathlib import Path

from playwright.async_api import BrowserContext, Page, TimeoutError as PWTimeout, async_playwright

from config import config

logger = logging.getLogger("worker.meet")

JOIN_SELECTORS = [
    'button:has-text("Join now")',
    'button:has-text("Ask to join")',
    '[aria-label="Join now"]',
    'span:has-text("Join now")',
]
NAME_SELECTORS = [
    'input[aria-label="Your name"]',
    'input[placeholder="Your name"]',
]
CAMERA_OFF_SELECTORS = [
    '[aria-label="Turn off camera"]',
    '[data-tooltip*="camera"]',
]
IN_MEETING_SELECTORS = [
    '[aria-label="Leave call"]',
    'button[aria-label="Leave call"]',
    '[aria-label*="Leave call"]',
]


class MeetController:
    def __init__(self) -> None:
        self._playwright = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        Path(config.chrome_user_data_dir).mkdir(parents=True, exist_ok=True)
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=config.chrome_user_data_dir,
            channel=config.chrome_channel,
            headless=config.headless,
            args=[
                "--use-fake-ui-for-media-stream",  # auto-accept mic/cam prompts
                "--disable-blink-features=AutomationControlled",
            ],
            permissions=["microphone", "camera"],
            viewport={"width": 1280, "height": 800},
        )
        await self._context.grant_permissions(
            ["microphone", "camera"], origin="https://meet.google.com"
        )
        logger.info("chrome launched with profile %s", config.chrome_user_data_dir)

    async def _click_first(self, page: Page, selectors: list[str], timeout: float = 4000) -> bool:
        for selector in selectors:
            try:
                await page.click(selector, timeout=timeout)
                logger.info("clicked selector: %s", selector)
                return True
            except PWTimeout:
                continue
            except Exception as exc:  # noqa: BLE001
                logger.debug("selector %s failed: %s", selector, exc)
        return False

    async def _fill_first(self, page: Page, selectors: list[str], value: str) -> bool:
        for selector in selectors:
            try:
                await page.fill(selector, value, timeout=3000)
                logger.info("filled selector: %s", selector)
                return True
            except Exception:  # noqa: BLE001
                continue
        return False

    async def join(self, meeting_url: str) -> None:
        if self._context is None:
            raise RuntimeError("MeetController not started")

        self._page = await self._context.new_page()
        page = self._page
        logger.info("navigating to %s", meeting_url)
        await page.goto(meeting_url, wait_until="networkidle")
        await page.wait_for_timeout(2500)

        # Guest name (only present when not signed in).
        await self._fill_first(page, NAME_SELECTORS, config.agent_display_name)

        # Camera off; keep mic on so the virtual device feeds Meet.
        await self._click_first(page, CAMERA_OFF_SELECTORS, timeout=2000)

        if not await self._click_first(page, JOIN_SELECTORS, timeout=8000):
            await self._screenshot("join_failed")
            raise RuntimeError("could not find a Join button on the Meet page")

    async def wait_until_in_meeting(self, timeout_ms: int = 60000) -> bool:
        if self._page is None:
            return False
        for selector in IN_MEETING_SELECTORS:
            try:
                await self._page.wait_for_selector(selector, timeout=timeout_ms)
                logger.info("in meeting (matched %s)", selector)
                return True
            except PWTimeout:
                continue
        await self._screenshot("in_meeting_timeout")
        return False

    async def _screenshot(self, tag: str) -> None:
        if self._page is None:
            return
        path = Path(config.chrome_user_data_dir).parent / f"meet_{tag}.png"
        try:
            await self._page.screenshot(path=str(path))
            logger.info("saved screenshot %s", path)
        except Exception as exc:  # noqa: BLE001
            logger.debug("screenshot failed: %s", exc)

    async def stop(self) -> None:
        if self._context is not None:
            await self._context.close()
        if self._playwright is not None:
            await self._playwright.stop()
        self._context = None
        self._playwright = None
        self._page = None
