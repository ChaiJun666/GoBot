from __future__ import annotations

from pathlib import Path

from app.core.database import Database
from app.schemas.lead import (
    EnrichedLead,
    IntelligenceFactors,
    LeadIntelligence,
    ScrapedLead,
)


def test_database_persists_job_lifecycle(tmp_path: Path) -> None:
    database = Database(tmp_path / "app.db")
    database.initialize()
    database.create_job(
        job_id="job-1",
        query="Restaurant Jakarta",
        query_config={"query": "Restaurant Jakarta"},
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


def test_database_persists_campaign_and_enriched_results(tmp_path: Path) -> None:
    database = Database(tmp_path / "app.db")
    database.initialize()
    database.create_job(
        job_id="job-2",
        campaign_id="campaign-1",
        query="Coffee shop Bandung",
        query_config={"query": "Coffee shop Bandung"},
        source="google_maps",
        max_results=5,
    )
    database.create_campaign(
        campaign_id="campaign-1",
        job_id="job-2",
        name="Bandung cafes",
        industry="restaurant",
        location="Bandung",
        query="Coffee shop Bandung",
        query_config={"query": "Coffee shop Bandung"},
        source="google_maps",
        max_results=5,
    )

    database.mark_campaign_running("campaign-1")
    database.complete_campaign(
        "campaign-1",
        [
            EnrichedLead(
                name="Lead One",
                address="Bandung",
                phone="08123456789",
                email="team@example.com",
                source="google_maps",
                intelligence=LeadIntelligence(
                    score=88,
                    category="A+ (Excellent)",
                    priority="HIGH",
                    recommendation="Priority lead - contact immediately with premium approach",
                    factors=IntelligenceFactors(
                        data_completeness=90,
                        business_quality=85,
                        digital_presence=80,
                        location_value=80,
                        industry_potential=83,
                        contactability=70,
                    ),
                ),
            )
        ],
        total_leads=1,
        average_score=88,
        priority_leads=1,
    )

    campaign = database.get_campaign("campaign-1")

    assert campaign is not None
    assert campaign["status"] == "completed"
    assert campaign["average_score"] == 88
    assert campaign["priority_leads"] == 1
    assert campaign["results"][0].intelligence.priority == "HIGH"
    assert campaign["results"][0].email == "team@example.com"


def test_database_retries_failed_job_and_campaign(tmp_path: Path) -> None:
    database = Database(tmp_path / "app.db")
    database.initialize()
    database.create_job(
        job_id="job-3",
        campaign_id="campaign-3",
        query="Dentist Shanghai",
        query_config={"query": "Dentist Shanghai"},
        source="google_maps",
        max_results=10,
    )
    database.create_campaign(
        campaign_id="campaign-3",
        job_id="job-3",
        name="Shanghai dentists",
        industry="healthcare",
        location="Shanghai",
        query="Dentist Shanghai",
        query_config={"query": "Dentist Shanghai"},
        source="google_maps",
        max_results=10,
    )

    database.fail_job("job-3", "network timeout")
    database.fail_campaign("campaign-3", "network timeout")

    database.retry_job("job-3")
    database.retry_campaign("campaign-3")

    job = database.get_job("job-3")
    campaign = database.get_campaign("campaign-3")

    assert job is not None
    assert campaign is not None
    assert job["status"] == "queued"
    assert job["result_count"] == 0
    assert job["error_message"] is None
    assert len(job["results"]) == 0
    assert campaign["status"] == "queued"
    assert campaign["total_leads"] == 0
    assert campaign["priority_leads"] == 0
    assert campaign["error_message"] is None
    assert len(campaign["results"]) == 0
