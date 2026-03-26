from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Any

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, async_playwright

from app.core.config import Settings
from app.core.database import Database
from app.schemas.linkedin import LinkedInSessionStatus

LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/"
LINKEDIN_SOURCE = "linkedin"
LINKEDIN_SESSION_COOKIE = "li_at"
LINKEDIN_LOGIN_TRANSITION_PATTERN = re.compile(r".*(feed|checkpoint|challenge|authwall|login).*")
LINKEDIN_AUTH_BLOCKERS = ("/login", "/authwall", "/checkpoint", "/challenge", "/uas/login")
LINKEDIN_AUTHENTICATED_PATHS = ("/feed", "/mynetwork", "/messaging", "/notifications")
WARM_UP_URLS = (
    "https://www.google.com",
    "https://www.wikipedia.org",
    "https://www.github.com",
)


@dataclass(slots=True)
class LoginAttempt:
    url: str


class LinkedInSessionService:
    def __init__(self, *, settings: Settings, database: Database) -> None:
        self.settings = settings
        self.database = database

    async def get_status(self) -> LinkedInSessionStatus:
        record = self.database.get_source_session(LINKEDIN_SOURCE)
        if record is None:
            return LinkedInSessionStatus(connected=False)

        cookies = record.get("cookies") or {}
        return LinkedInSessionStatus(
            connected=bool(cookies.get(LINKEDIN_SESSION_COOKIE)),
            account_label=record.get("account_label"),
            last_error=record.get("last_error"),
            updated_at=record.get("updated_at"),
        )

    async def connect(self, *, username: str, password: str) -> LinkedInSessionStatus:
        try:
            cookies, login_response = await self._login(username=username, password=password)
            if LINKEDIN_SESSION_COOKIE not in cookies:
                raise RuntimeError(self._build_login_failure_message(login_response, cookies))

            self.database.upsert_source_session(
                source=LINKEDIN_SOURCE,
                cookies=cookies,
                account_label=username,
                last_error=None,
            )
            return await self.get_status()
        except Exception as exc:
            self.database.upsert_source_session(
                source=LINKEDIN_SOURCE,
                cookies={},
                account_label=username,
                last_error=str(exc),
            )
            raise

    async def disconnect(self) -> LinkedInSessionStatus:
        self.database.delete_source_session(LINKEDIN_SOURCE)
        return LinkedInSessionStatus(connected=False)

    def require_cookies(self) -> dict[str, str]:
        record = self.database.get_source_session(LINKEDIN_SOURCE)
        if record is None:
            raise RuntimeError("LinkedIn session is not connected")
        cookies = record.get("cookies") or {}
        if LINKEDIN_SESSION_COOKIE not in cookies:
            raise RuntimeError("LinkedIn session is not connected")
        return cookies

    async def _login(self, *, username: str, password: str) -> tuple[dict[str, str], LoginAttempt]:
        timeout_ms = max(self.settings.scraper_timeout_ms, 1_000)

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=self.settings.scraper_user_agent,
                locale="en-US",
            )
            page = await context.new_page()

            try:
                await self._warm_up_browser(page)
                await page.goto(LINKEDIN_LOGIN_URL, wait_until="domcontentloaded", timeout=timeout_ms)

                try:
                    await page.wait_for_selector("#username", state="visible", timeout=timeout_ms)
                except PlaywrightTimeoutError as exc:
                    raise RuntimeError("LinkedIn login form not found") from exc

                await page.fill("#username", username)
                await page.fill("#password", password)
                await page.click('button[type="submit"]')

                try:
                    await page.wait_for_url(LINKEDIN_LOGIN_TRANSITION_PATTERN, timeout=timeout_ms)
                except PlaywrightTimeoutError as exc:
                    if "login" in page.url:
                        raise RuntimeError(
                            "LinkedIn login failed: the page stayed on the login screen after submit"
                        ) from exc

                self._raise_if_auth_blocked(page.url)
                await self._verify_logged_in(page)

                cookies = self._extract_browser_cookies(await context.cookies())
                return cookies, LoginAttempt(url=page.url)
            finally:
                await context.close()
                await browser.close()

    async def _warm_up_browser(self, page: Page) -> None:
        for url in WARM_UP_URLS:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=10_000)
                await asyncio.sleep(1)
            except Exception:
                continue

    def _raise_if_auth_blocked(self, current_url: str) -> None:
        lowered = current_url.lower()
        if "/checkpoint" in lowered or "/challenge" in lowered:
            raise RuntimeError(
                f"LinkedIn security checkpoint detected. Please verify the account manually first. Current URL: {current_url}"
            )
        if "/authwall" in lowered:
            raise RuntimeError(
                f"LinkedIn auth wall detected. LinkedIn is blocking automated login. Current URL: {current_url}"
            )
        if "/login" in lowered and LINKEDIN_FEED_URL not in lowered:
            raise RuntimeError("LinkedIn login failed: credentials may be invalid")

    async def _verify_logged_in(self, page: Page) -> None:
        deadline_attempts = 10
        for _ in range(deadline_attempts):
            if await self._is_logged_in(page):
                return
            await asyncio.sleep(0.5)

    async def _is_logged_in(self, page: Page) -> bool:
        current_url = page.url.lower()
        if any(pattern in current_url for pattern in LINKEDIN_AUTH_BLOCKERS):
            return False

        selectors = (
            ".global-nav__primary-link",
            '[data-control-name="nav.settings"]',
            'nav a[href*="/feed"]',
            'nav button:has-text("Home")',
            'nav a[href*="/mynetwork"]',
        )
        for selector in selectors:
            try:
                if await page.locator(selector).count() > 0:
                    return True
            except Exception:
                continue

        return any(pattern in current_url for pattern in LINKEDIN_AUTHENTICATED_PATHS)

    def _extract_browser_cookies(self, cookies: list[dict[str, Any]]) -> dict[str, str]:
        return {
            str(cookie["name"]): str(cookie["value"])
            for cookie in cookies
            if cookie.get("domain") and "linkedin.com" in str(cookie["domain"])
        }

    def _build_login_failure_message(self, response: Any, cookies: dict[str, str]) -> str:
        url = str(getattr(response, "url", LINKEDIN_LOGIN_URL))
        cookie_keys = ", ".join(sorted(cookies)) or "none"
        return f"LinkedIn login failed: no li_at cookie found after redirect to {url} (cookies: {cookie_keys})"
