from __future__ import annotations

from typing import Any

from scrapling import AsyncFetcher

from app.core.config import Settings
from app.core.database import Database
from app.schemas.linkedin import LinkedInSessionStatus

LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
LINKEDIN_LOGIN_SUBMIT_URL = "https://www.linkedin.com/checkpoint/lg/login-submit"
LINKEDIN_SOURCE = "linkedin"
LINKEDIN_SESSION_COOKIE = "li_at"


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
            login_page = await self._fetch(LOGIN_METHOD.GET, LINKEDIN_LOGIN_URL)
            csrf_token = self._extract_login_csrf(login_page)
            initial_cookies = self._to_cookie_dict(getattr(login_page, "cookies", {}))

            login_response = await self._fetch(
                LOGIN_METHOD.POST,
                LINKEDIN_LOGIN_SUBMIT_URL,
                cookies=initial_cookies,
                data={
                    "session_key": username,
                    "session_password": password,
                    "loginCsrfParam": csrf_token,
                },
            )
            cookies = {
                **initial_cookies,
                **self._to_cookie_dict(getattr(login_response, "cookies", {})),
            }
            if LINKEDIN_SESSION_COOKIE not in cookies:
                raise RuntimeError("LinkedIn login failed or session cookie was not returned")

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

    async def _fetch(
        self,
        method: "LOGIN_METHOD",
        url: str,
        *,
        cookies: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
    ) -> Any:
        kwargs = {
            "headers": {
                "User-Agent": self.settings.scraper_user_agent,
                "Accept-Language": "en-US,en;q=0.9",
            },
            "timeout": max(self.settings.scraper_timeout_ms / 1000, 1),
            "verify": self.settings.scraper_verify_tls,
            "cookies": cookies,
            "follow_redirects": True,
        }
        if method is LOGIN_METHOD.GET:
            return await AsyncFetcher.get(url, **kwargs)
        return await AsyncFetcher.post(url, data=data, **kwargs)

    def _extract_login_csrf(self, response: Any) -> str:
        token = response.css('input[name="loginCsrfParam"]::attr(value)').get()
        if not token:
            raise RuntimeError("LinkedIn login CSRF token not found")
        return str(token)

    def _to_cookie_dict(self, cookies: Any) -> dict[str, str]:
        if isinstance(cookies, dict):
            return {str(key): str(value) for key, value in cookies.items()}
        if isinstance(cookies, tuple):
            parsed: dict[str, str] = {}
            for cookie in cookies:
                if isinstance(cookie, dict) and "name" in cookie and "value" in cookie:
                    parsed[str(cookie["name"])] = str(cookie["value"])
            return parsed
        return {}


class LOGIN_METHOD:
    GET = "GET"
    POST = "POST"
