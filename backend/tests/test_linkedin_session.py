from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.database import Database
from app.services.scraping.linkedin_session import LinkedInSessionService


class _CssResult:
    def __init__(self, value: str | None) -> None:
        self.value = value

    def get(self) -> str | None:
        return self.value


class _DummyResponse:
    def __init__(self, *, csrf: str | None = None, cookies: dict[str, str] | None = None) -> None:
        self._csrf = csrf
        self.cookies = cookies or {}

    def css(self, _selector: str) -> _CssResult:
        return _CssResult(self._csrf)


def _build_service(tmp_path: Path) -> LinkedInSessionService:
    database = Database(tmp_path / "linkedin-session.db")
    database.initialize()
    return LinkedInSessionService(settings=Settings(), database=database)


def test_linkedin_session_connects_and_persists_shared_cookies(tmp_path: Path) -> None:
    service = _build_service(tmp_path)

    async def fake_fetch(
        method: str,
        url: str,
        *,
        cookies: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
    ) -> _DummyResponse:
        if "login-submit" in url:
            assert cookies == {"JSESSIONID": "seed-cookie"}
            assert data is not None
            assert data["session_key"] == "user@example.com"
            return _DummyResponse(cookies={"li_at": "linkedin-cookie", "JSESSIONID": "fresh-cookie"})

        return _DummyResponse(csrf="csrf-token", cookies={"JSESSIONID": "seed-cookie"})

    service._fetch = fake_fetch  # type: ignore[method-assign]

    status = asyncio.run(service.connect(username="user@example.com", password="secret"))

    assert status.connected is True
    assert status.account_label == "user@example.com"
    assert service.require_cookies()["li_at"] == "linkedin-cookie"


def test_linkedin_session_persists_last_error_on_failed_connect(tmp_path: Path) -> None:
    service = _build_service(tmp_path)

    async def fake_fetch(
        _method: str,
        url: str,
        *,
        cookies: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
    ) -> _DummyResponse:
        if "login-submit" in url:
            return _DummyResponse(cookies={"JSESSIONID": "fresh-cookie"})

        return _DummyResponse(csrf="csrf-token", cookies={"JSESSIONID": "seed-cookie"})

    service._fetch = fake_fetch  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="session cookie"):
        asyncio.run(service.connect(username="user@example.com", password="secret"))

    status = asyncio.run(service.get_status())
    assert status.connected is False
    assert status.account_label == "user@example.com"
    assert status.last_error is not None
