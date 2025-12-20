"""Playwright harness (stub) for browser-based verification and flows.

Notes:
- This is a lightweight wrapper; real usage requires Playwright to be installed.
- Provides basic navigation, DOM snapshot, and screenshot capture.
- Scoped to respect RunContext controls (scope, ACL, kill-switch).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page

    from secbrain.core.context import RunContext


@dataclass
class PageArtifact:
    url: str
    title: str
    html: str
    screenshot_path: Path | None
    console_messages: list[str]


class PlaywrightClient:
    """Minimal async Playwright wrapper with scope checks."""

    def __init__(self, run_context: RunContext, headless: bool = True, navigation_timeout_ms: int = 15000):
        self.run_context = run_context
        self.headless = headless
        self.navigation_timeout_ms = navigation_timeout_ms
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def _ensure_browser(self) -> None:
        if self._browser:
            return
        try:
            from playwright.async_api import async_playwright
        except Exception as e:
            raise RuntimeError("Playwright not available. Install playwright + browsers.") from e

        p = await async_playwright().start()
        self._browser = await p.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context()
        self._page = await self._context.new_page()
        self._page.set_default_timeout(self.navigation_timeout_ms)

    async def close(self) -> None:
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
        finally:
            self._browser = None
            self._context = None
            self._page = None

    async def navigate_and_capture(self, url: str, screenshot_dir: Path | None = None) -> PageArtifact:
        """Navigate to a URL and capture DOM + screenshot."""
        if self.run_context.is_killed():
            raise RuntimeError("Kill-switch activated")
        if not self.run_context.check_scope(url):
            raise RuntimeError(f"URL not in scope: {url}")
        if not self.run_context.check_tool_acl("playwright"):
            raise RuntimeError("Playwright not allowed in this phase")

        await self.run_context.acquire_rate_limit("playwright")
        await self._ensure_browser()

        assert self._page
        console_messages: list[str] = []
        self._page.on("console", lambda msg: console_messages.append(msg.text))

        await self._page.goto(url, wait_until="domcontentloaded")
        title = await self._page.title()
        html = await self._page.content()

        screenshot_path = None
        if screenshot_dir:
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = screenshot_dir / "page.png"
            await self._page.screenshot(path=str(screenshot_path), full_page=True)

        return PageArtifact(
            url=url,
            title=title,
            html=html,
            screenshot_path=screenshot_path,
            console_messages=console_messages[:50],
        )


async def create_playwright_client(run_context: RunContext, **kwargs: Any) -> PlaywrightClient:
    """Factory for PlaywrightClient with config overrides."""
    headless = kwargs.get("headless", True)
    nav_timeout = kwargs.get("navigation_timeout_ms", 15000)
    return PlaywrightClient(run_context, headless=headless, navigation_timeout_ms=nav_timeout)
