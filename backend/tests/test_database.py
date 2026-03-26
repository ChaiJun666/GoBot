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


def test_database_persists_mailboxes_messages_and_lead_recipients(tmp_path: Path) -> None:
    database = Database(tmp_path / "app.db")
    database.initialize()

    database.create_job(
        job_id="job-mail",
        campaign_id="campaign-mail",
        query="Design agencies Berlin",
        query_config={"query": "Design agencies Berlin"},
        source="google_maps",
        max_results=10,
    )
    database.create_campaign(
        campaign_id="campaign-mail",
        job_id="job-mail",
        name="Berlin agencies",
        industry="professional",
        location="Berlin",
        query="Design agencies Berlin",
        query_config={"query": "Design agencies Berlin"},
        source="google_maps",
        max_results=10,
    )
    database.complete_campaign(
        "campaign-mail",
        [
            EnrichedLead(
                name="Studio North",
                address="Berlin",
                email="hello@studionorth.example",
                current_company="Studio North",
                source="google_maps",
                intelligence=LeadIntelligence(
                    score=84,
                    category="A (Strong)",
                    priority="HIGH",
                    recommendation="Worth immediate outreach",
                    factors=IntelligenceFactors(
                        data_completeness=85,
                        business_quality=80,
                        digital_presence=78,
                        location_value=82,
                        industry_potential=88,
                        contactability=90,
                    ),
                ),
            )
        ],
        total_leads=1,
        average_score=84,
        priority_leads=1,
    )

    database.create_mailbox(
        mailbox_id="mailbox-1",
        provider="gmail",
        email_address="sales@example.com",
        note="Primary outreach",
        imap_host="imap.gmail.com",
        imap_port=993,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_starttls=True,
        encrypted_auth_secret="encrypted-secret",
    )
    database.mark_mailbox_ready("mailbox-1")
    database.upsert_mail_message(
        message_id="mailbox-1:inbox:1",
        mailbox_id="mailbox-1",
        folder="inbox",
        remote_uid="1",
        message_id_header="<message-1@example.com>",
        subject="Hello from Berlin",
        from_name="Studio North",
        from_address="hello@studionorth.example",
        to_summary="sales@example.com",
        snippet="Checking in",
        body_text="Checking in about your services.",
        is_read=False,
        sent_at="2026-03-26T01:00:00+00:00",
        received_at="2026-03-26T01:01:00+00:00",
    )

    mailbox = database.get_mailbox("mailbox-1")
    messages = database.list_mail_messages(mailbox_id="mailbox-1", folder="inbox", limit=20)
    message = database.get_mail_message("mailbox-1:inbox:1")
    recipients = database.list_lead_recipients(limit=20)

    assert mailbox is not None
    assert mailbox["email_address"] == "sales@example.com"
    assert mailbox["smtp_starttls"] is True
    assert len(messages) == 1
    assert messages[0]["subject"] == "Hello from Berlin"
    assert message is not None
    assert message["message_id"] == "<message-1@example.com>"
    assert recipients == [
        {
            "id": "campaign-mail:hello@studionorth.example",
            "email": "hello@studionorth.example",
            "lead_name": "Studio North",
            "campaign_id": "campaign-mail",
            "campaign_name": "Berlin agencies",
            "source": "google_maps",
            "company": "Studio North",
        }
    ]
