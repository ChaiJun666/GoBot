from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.database import Database
from app.services.scraping.linkedin_session import LinkedInSessionService


class _DummyResponse:
    def __init__(self, url: str = "https://www.linkedin.com/feed/") -> None:
        self.url = url


def _build_service(tmp_path: Path) -> LinkedInSessionService:
    database = Database(tmp_path / "linkedin-session.db")
    database.initialize()
    return LinkedInSessionService(settings=Settings(), database=database)


def test_linkedin_session_connects_and_persists_shared_cookies(tmp_path: Path) -> None:
    service = _build_service(tmp_path)

    async def fake_login(*, username: str, password: str) -> tuple[dict[str, str], _DummyResponse]:
        assert username == "user@example.com"
        assert password == "secret"
        return (
            {"li_at": "linkedin-cookie", "JSESSIONID": "fresh-cookie"},
            _DummyResponse(),
        )

    service._login = fake_login  # type: ignore[method-assign]

    status = asyncio.run(service.connect(username="user@example.com", password="secret"))

    assert status.connected is True
    assert status.account_label == "user@example.com"
    assert service.require_cookies()["li_at"] == "linkedin-cookie"


def test_linkedin_session_persists_last_error_on_failed_connect(tmp_path: Path) -> None:
    service = _build_service(tmp_path)

    async def fake_login(*, username: str, password: str) -> tuple[dict[str, str], _DummyResponse]:
        assert username == "user@example.com"
        assert password == "secret"
        return (
            {"JSESSIONID": "fresh-cookie"},
            _DummyResponse("https://www.linkedin.com/feed/"),
        )

    service._login = fake_login  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="no li_at cookie"):
        asyncio.run(service.connect(username="user@example.com", password="secret"))

    status = asyncio.run(service.get_status())
    assert status.connected is False
    assert status.account_label == "user@example.com"
    assert status.last_error is not None
