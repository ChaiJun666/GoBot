from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.router import api_router
from app.core.database import Database
from app.schemas.lead import ScrapedLead


class _DummyJobManager:
    def __init__(self) -> None:
        self.enqueued: list[str] = []

    async def enqueue(self, job_id: str) -> None:
        self.enqueued.append(job_id)


def _create_test_app(db_path: Path) -> tuple[FastAPI, Database, _DummyJobManager]:
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")

    database = Database(db_path)
    database.initialize()
    job_manager = _DummyJobManager()

    app.state.database = database
    app.state.job_manager = job_manager

    return app, database, job_manager


def test_retry_scrape_job_resets_failed_job_and_campaign(tmp_path: Path) -> None:
    app, database, job_manager = _create_test_app(tmp_path / "retry-job.db")

    database.create_job(
        job_id="job-1",
        campaign_id="campaign-1",
        query="Best ramen Tokyo",
        query_config={"query": "Best ramen Tokyo"},
        source="google_maps",
        max_results=10,
    )
    database.create_campaign(
        campaign_id="campaign-1",
        job_id="job-1",
        name="Tokyo ramen",
        industry="restaurant",
        location="Tokyo",
        query="Best ramen Tokyo",
        query_config={"query": "Best ramen Tokyo"},
        source="google_maps",
        max_results=10,
    )
    database.complete_job(
        "job-1",
        [ScrapedLead(name="Old Lead", address="Tokyo", email="old@example.com", source="google_maps")],
    )
    database.fail_job("job-1", "temporary failure")
    database.fail_campaign("campaign-1", "temporary failure")

    with TestClient(app) as client:
        response = client.post("/api/v1/scrape-jobs/job-1/retry")

    assert response.status_code == 202
    payload = response.json()
    assert payload["id"] == "job-1"
    assert payload["status"] == "queued"
    assert job_manager.enqueued == ["job-1"]

    refreshed_job = database.get_job("job-1")
    refreshed_campaign = database.get_campaign("campaign-1")

    assert refreshed_job is not None
    assert refreshed_campaign is not None
    assert refreshed_job["result_count"] == 0
    assert len(refreshed_job["results"]) == 0
    assert refreshed_campaign["status"] == "queued"
    assert refreshed_campaign["total_leads"] == 0


def test_retry_campaign_requeues_failed_campaign(tmp_path: Path) -> None:
    app, database, job_manager = _create_test_app(tmp_path / "retry-campaign.db")

    database.create_job(
        job_id="job-2",
        campaign_id="campaign-2",
        query="Lisbon coworking",
        query_config={"query": "Lisbon coworking"},
        source="google_maps",
        max_results=15,
    )
    database.create_campaign(
        campaign_id="campaign-2",
        job_id="job-2",
        name="Lisbon coworking",
        industry="professional",
        location="Lisbon",
        query="Lisbon coworking",
        query_config={"query": "Lisbon coworking"},
        source="google_maps",
        max_results=15,
    )
    database.fail_job("job-2", "scraper blocked")
    database.fail_campaign("campaign-2", "scraper blocked")

    with TestClient(app) as client:
        response = client.post("/api/v1/campaigns/campaign-2/retry")

    assert response.status_code == 202
    payload = response.json()
    assert payload["id"] == "campaign-2"
    assert payload["status"] == "queued"
    assert job_manager.enqueued == ["job-2"]

    refreshed_job = database.get_job("job-2")
    assert refreshed_job is not None
    assert refreshed_job["status"] == "queued"
