from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.router import api_router
from app.core.config import Settings
from app.core.database import Database
from app.services.scraping.linkedin_session import LinkedInSessionService


def _create_test_app(db_path: Path) -> tuple[FastAPI, LinkedInSessionService]:
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")

    database = Database(db_path)
    database.initialize()
    service = LinkedInSessionService(settings=Settings(), database=database)

    app.state.database = database
    app.state.job_manager = None
    app.state.linkedin_session_service = service

    return app, service


def test_connect_linkedin_session_returns_400_for_login_failures(tmp_path: Path) -> None:
    app, service = _create_test_app(tmp_path / "linkedin-api.db")

    async def fake_connect(*, username: str, password: str):
        raise RuntimeError(f"LinkedIn login failed for {username}")

    service.connect = fake_connect  # type: ignore[method-assign]

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/linkedin/session",
            json={"username": "user@example.com", "password": "secret"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "LinkedIn login failed for user@example.com"
