from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.router import api_router
from app.core.database import Database
from app.schemas.lead import EnrichedLead, IntelligenceFactors, LeadIntelligence
from app.schemas.mail import MailboxSummary, MailboxSyncResponse
from app.services.mail.service import MailService


class _DummyCipher:
    def encrypt(self, value: str) -> str:
        return f"enc::{value}"

    def decrypt(self, value: str) -> str:
        return value.removeprefix("enc::")


class _DummySMTP:
    def __init__(self) -> None:
        self.logged_in_with: tuple[str, str] | None = None
        self.sent_subjects: list[str] = []
        self.quit_called = False

    def login(self, username: str, password: str) -> None:
        self.logged_in_with = (username, password)

    def send_message(self, message) -> None:  # type: ignore[no-untyped-def]
        self.sent_subjects.append(str(message["Subject"]))

    def quit(self) -> None:
        self.quit_called = True


def _create_test_app(db_path: Path) -> tuple[FastAPI, Database, MailService]:
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")

    database = Database(db_path)
    database.initialize()
    mail_service = MailService(database=database, cipher=_DummyCipher())

    app.state.database = database
    app.state.mail_service = mail_service

    return app, database, mail_service


def test_list_mail_providers_returns_presets(tmp_path: Path) -> None:
    app, _, _ = _create_test_app(tmp_path / "mail-providers.db")

    with TestClient(app) as client:
        response = client.get("/api/v1/mail/providers")

    assert response.status_code == 200
    payload = response.json()
    assert any(provider["key"] == "gmail" for provider in payload)
    assert any(provider["key"] == "qq" for provider in payload)


def test_create_mailbox_and_send_mail(tmp_path: Path) -> None:
    app, database, mail_service = _create_test_app(tmp_path / "mail-send.db")
    smtp_client = _DummySMTP()

    def fake_sync_mailbox(mailbox_id: str, *, limit: int = 50) -> MailboxSyncResponse:
        database.mark_mailbox_ready(mailbox_id)
        mailbox = database.get_mailbox(mailbox_id)
        assert mailbox is not None
        return MailboxSyncResponse(
            mailbox=MailboxSummary.from_record(mailbox),
            inbox_count=0,
            sent_count=0,
        )

    def fake_create_smtp_client(*, host: str, port: int, use_starttls: bool) -> _DummySMTP:
        assert host == "smtp.gmail.com"
        assert port == 587
        assert use_starttls is True
        return smtp_client

    mail_service.sync_mailbox = fake_sync_mailbox  # type: ignore[method-assign]
    mail_service._create_smtp_client = fake_create_smtp_client  # type: ignore[method-assign]

    with TestClient(app) as client:
        create_response = client.post(
            "/api/v1/mail/mailboxes",
            json={
                "provider": "gmail",
                "email_address": "sales@example.com",
                "auth_secret": "app-password",
                "note": "Primary outreach",
            },
        )

        assert create_response.status_code == 201
        mailbox_id = create_response.json()["id"]

        send_response = client.post(
            "/api/v1/mail/send",
            json={
                "mailbox_id": mailbox_id,
                "to": ["lead@example.com"],
                "subject": "Hello there",
                "body": "Checking in about your campaign.",
            },
        )

    assert send_response.status_code == 202
    payload = send_response.json()
    assert payload["accepted"] == ["lead@example.com"]
    assert smtp_client.logged_in_with == ("sales@example.com", "app-password")
    assert smtp_client.sent_subjects == ["Hello there"]
    assert smtp_client.quit_called is True


def test_list_lead_recipients_returns_campaign_emails(tmp_path: Path) -> None:
    app, database, _ = _create_test_app(tmp_path / "lead-recipients.db")

    database.create_job(
        job_id="job-1",
        campaign_id="campaign-1",
        query="SaaS founders London",
        query_config={"query": "SaaS founders London"},
        source="linkedin",
        max_results=10,
    )
    database.create_campaign(
        campaign_id="campaign-1",
        job_id="job-1",
        name="London founders",
        industry="professional",
        location="London",
        query="SaaS founders London",
        query_config={"query": "SaaS founders London"},
        source="linkedin",
        max_results=10,
    )
    database.complete_campaign(
        "campaign-1",
        [
            EnrichedLead(
                name="Jamie Stone",
                address="London",
                email="jamie@example.com",
                current_company="Northstar Labs",
                source="linkedin",
                intelligence=LeadIntelligence(
                    score=90,
                    category="A+ (Excellent)",
                    priority="HIGH",
                    recommendation="Priority lead",
                    factors=IntelligenceFactors(
                        data_completeness=95,
                        business_quality=88,
                        digital_presence=86,
                        location_value=82,
                        industry_potential=91,
                        contactability=98,
                    ),
                ),
            )
        ],
        total_leads=1,
        average_score=90,
        priority_leads=1,
    )

    with TestClient(app) as client:
        response = client.get("/api/v1/mail/lead-recipients")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "campaign-1:jamie@example.com",
            "email": "jamie@example.com",
            "lead_name": "Jamie Stone",
            "campaign_id": "campaign-1",
            "campaign_name": "London founders",
            "source": "linkedin",
            "company": "Northstar Labs",
        }
    ]
