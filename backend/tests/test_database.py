from __future__ import annotations

from pathlib import Path

from app.core.database import Database
from app.schemas.lead import ScrapedLead


def test_database_persists_job_lifecycle(tmp_path: Path) -> None:
    database = Database(tmp_path / "app.db")
    database.initialize()
    database.create_job(
        job_id="job-1",
        query="Restaurant Jakarta",
        source="google_maps",
        max_results=10,
    )

    database.mark_job_running("job-1")
    database.complete_job(
        "job-1",
        [
            ScrapedLead(
                name="Lead One",
                address="Jakarta",
                phone="08123456789",
                source="google_maps",
            )
        ],
    )

    job = database.get_job("job-1")

    assert job is not None
    assert job["status"] == "completed"
    assert job["result_count"] == 1
    assert len(job["results"]) == 1
    assert job["results"][0].name == "Lead One"
