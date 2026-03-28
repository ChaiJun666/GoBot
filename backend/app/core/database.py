from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import sqlite3
import threading
from typing import Any

from app.schemas.lead import EnrichedLead, ScrapedLead


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._lock = threading.Lock()

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS scrape_jobs (
                    id TEXT PRIMARY KEY,
                    campaign_id TEXT,
                    query TEXT NOT NULL,
                    query_config_json TEXT NOT NULL DEFAULT '{}',
                    source TEXT NOT NULL,
                    max_results INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    result_count INTEGER NOT NULL DEFAULT 0,
                    results_json TEXT NOT NULL DEFAULT '[]',
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_scrape_jobs_created_at
                ON scrape_jobs(created_at DESC);

                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    location TEXT NOT NULL,
                    query TEXT NOT NULL,
                    query_config_json TEXT NOT NULL DEFAULT '{}',
                    source TEXT NOT NULL,
                    max_results INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    total_leads INTEGER NOT NULL DEFAULT 0,
                    average_score INTEGER NOT NULL DEFAULT 0,
                    priority_leads INTEGER NOT NULL DEFAULT 0,
                    results_json TEXT NOT NULL DEFAULT '[]',
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_campaigns_created_at
                ON campaigns(created_at DESC);

                CREATE TABLE IF NOT EXISTS source_sessions (
                    source TEXT PRIMARY KEY,
                    account_label TEXT,
                    cookies_json TEXT NOT NULL DEFAULT '{}',
                    last_error TEXT,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS mailboxes (
                    id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    email_address TEXT NOT NULL UNIQUE,
                    note TEXT,
                    imap_host TEXT NOT NULL,
                    imap_port INTEGER NOT NULL,
                    smtp_host TEXT NOT NULL,
                    smtp_port INTEGER NOT NULL,
                    smtp_starttls INTEGER NOT NULL DEFAULT 0,
                    encrypted_auth_secret TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ready',
                    last_error TEXT,
                    last_synced_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_mailboxes_created_at
                ON mailboxes(created_at DESC);

                CREATE TABLE IF NOT EXISTS mail_messages (
                    id TEXT PRIMARY KEY,
                    mailbox_id TEXT NOT NULL,
                    folder TEXT NOT NULL,
                    remote_uid TEXT NOT NULL,
                    message_id_header TEXT,
                    subject TEXT NOT NULL,
                    from_name TEXT,
                    from_address TEXT,
                    to_summary TEXT,
                    snippet TEXT,
                    body_text TEXT,
                    is_read INTEGER NOT NULL DEFAULT 0,
                    sent_at TEXT,
                    received_at TEXT,
                    synced_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(mailbox_id, folder, remote_uid)
                );
                CREATE INDEX IF NOT EXISTS idx_mail_messages_mailbox_folder_received
                ON mail_messages(mailbox_id, folder, received_at DESC, sent_at DESC, created_at DESC);

                CREATE TABLE IF NOT EXISTS llm_configs (
                    id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    base_url TEXT NOT NULL,
                    official_url TEXT,
                    note TEXT,
                    encrypted_api_key TEXT,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_llm_configs_display_name
                ON llm_configs(display_name);

                CREATE TABLE IF NOT EXISTS sites (
                    id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    slug TEXT NOT NULL UNIQUE,
                    domain TEXT NOT NULL,
                    note TEXT,
                    server_ip TEXT NOT NULL,
                    ssh_user TEXT NOT NULL,
                    encrypted_ssh_password TEXT NOT NULL,
                    wp_admin_user TEXT NOT NULL DEFAULT 'admin',
                    encrypted_wp_admin_password TEXT,
                    wp_admin_email TEXT NOT NULL,
                    mysql_database TEXT NOT NULL,
                    mysql_user TEXT NOT NULL,
                    encrypted_mysql_password TEXT NOT NULL,
                    encrypted_mysql_root_password TEXT NOT NULL,
                    ssl_mode TEXT NOT NULL DEFAULT 'none',
                    cloudflare_zone_id TEXT,
                    encrypted_cloudflare_api_token TEXT,
                    cloudflare_dns_proxy INTEGER NOT NULL DEFAULT 0,
                    wp_plugins_json TEXT NOT NULL DEFAULT '[]',
                    status TEXT NOT NULL DEFAULT 'draft',
                    deploy_log TEXT,
                    site_url TEXT,
                    wp_admin_url TEXT,
                    deployed_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_sites_created_at
                ON sites(created_at DESC);

                CREATE TABLE IF NOT EXISTS site_deployments (
                    id TEXT PRIMARY KEY,
                    site_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    log TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY (site_id) REFERENCES sites(id)
                );
                CREATE INDEX IF NOT EXISTS idx_site_deployments_site
                ON site_deployments(site_id, created_at DESC);
                """
            )
            self._ensure_column(connection, "scrape_jobs", "campaign_id", "TEXT")
            self._ensure_column(connection, "scrape_jobs", "query_config_json", "TEXT NOT NULL DEFAULT '{}'")
            self._ensure_column(connection, "campaigns", "query_config_json", "TEXT NOT NULL DEFAULT '{}'")

    def healthcheck(self) -> bool:
        try:
            with self._connect() as connection:
                connection.execute("SELECT 1")
            return True
        except sqlite3.Error:
            return False

    def create_job(
        self,
        *,
        job_id: str,
        query: str,
        query_config: dict[str, Any] | None,
        source: str,
        max_results: int,
        campaign_id: str | None = None,
    ) -> None:
        now = utc_now_iso()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scrape_jobs (
                    id, campaign_id, query, source, max_results, status, result_count,
                    query_config_json, results_json, error_message, created_at, started_at, completed_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    campaign_id,
                    query,
                    source,
                    max_results,
                    "queued",
                    0,
                    json.dumps(query_config or {}),
                    "[]",
                    None,
                    now,
                    None,
                    None,
                    now,
                ),
            )

    def create_campaign(
        self,
        *,
        campaign_id: str,
        job_id: str,
        name: str,
        industry: str,
        location: str,
        query: str,
        query_config: dict[str, Any] | None,
        source: str,
        max_results: int,
    ) -> None:
        now = utc_now_iso()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO campaigns (
                    id, job_id, name, industry, location, query, source, max_results, status,
                    query_config_json, total_leads, average_score, priority_leads, results_json, error_message,
                    created_at, started_at, completed_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    campaign_id,
                    job_id,
                    name,
                    industry,
                    location,
                    query,
                    source,
                    max_results,
                    "queued",
                    json.dumps(query_config or {}),
                    0,
                    0,
                    0,
                    "[]",
                    None,
                    now,
                    None,
                    None,
                    now,
                ),
            )

    def mark_job_running(self, job_id: str) -> None:
        now = utc_now_iso()
        self._update_record(
            "scrape_jobs",
            "id",
            job_id,
            status="running",
            started_at=now,
            updated_at=now,
            error_message=None,
        )

    def complete_job(self, job_id: str, results: list[ScrapedLead]) -> None:
        now = utc_now_iso()
        self._update_record(
            "scrape_jobs",
            "id",
            job_id,
            status="completed",
            completed_at=now,
            updated_at=now,
            result_count=len(results),
            results_json=json.dumps([lead.model_dump(mode="json") for lead in results]),
            error_message=None,
        )

    def fail_job(self, job_id: str, error_message: str) -> None:
        now = utc_now_iso()
        self._update_record(
            "scrape_jobs",
            "id",
            job_id,
            status="failed",
            completed_at=now,
            updated_at=now,
            error_message=error_message,
        )

    def retry_job(self, job_id: str) -> None:
        now = utc_now_iso()
        self._update_record(
            "scrape_jobs",
            "id",
            job_id,
            status="queued",
            result_count=0,
            results_json="[]",
            error_message=None,
            started_at=None,
            completed_at=None,
            updated_at=now,
        )

    def mark_campaign_running(self, campaign_id: str) -> None:
        now = utc_now_iso()
        self._update_record(
            "campaigns",
            "id",
            campaign_id,
            status="running",
            started_at=now,
            updated_at=now,
            error_message=None,
        )

    def complete_campaign(
        self,
        campaign_id: str,
        results: list[EnrichedLead],
        *,
        total_leads: int,
        average_score: int,
        priority_leads: int,
    ) -> None:
        now = utc_now_iso()
        self._update_record(
            "campaigns",
            "id",
            campaign_id,
            status="completed",
            completed_at=now,
            updated_at=now,
            total_leads=total_leads,
            average_score=average_score,
            priority_leads=priority_leads,
            results_json=json.dumps([lead.model_dump(mode="json") for lead in results]),
            error_message=None,
        )

    def fail_campaign(self, campaign_id: str, error_message: str) -> None:
        now = utc_now_iso()
        self._update_record(
            "campaigns",
            "id",
            campaign_id,
            status="failed",
            completed_at=now,
            updated_at=now,
            error_message=error_message,
        )

    def retry_campaign(self, campaign_id: str) -> None:
        now = utc_now_iso()
        self._update_record(
            "campaigns",
            "id",
            campaign_id,
            status="queued",
            total_leads=0,
            average_score=0,
            priority_leads=0,
            results_json="[]",
            error_message=None,
            started_at=None,
            completed_at=None,
            updated_at=now,
        )

    def list_jobs(self, *, limit: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, campaign_id, query, query_config_json, source, max_results, status, result_count, results_json,
                       error_message, created_at, started_at, completed_at, updated_at
                FROM scrape_jobs
                ORDER BY datetime(created_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_job_record(row) for row in rows]

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, campaign_id, query, query_config_json, source, max_results, status, result_count, results_json,
                       error_message, created_at, started_at, completed_at, updated_at
                FROM scrape_jobs
                WHERE id = ?
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_job_record(row)

    def list_campaigns(self, *, limit: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, job_id, name, industry, location, query, query_config_json, source, max_results, status,
                       total_leads, average_score, priority_leads, results_json, error_message,
                       created_at, started_at, completed_at, updated_at
                FROM campaigns
                ORDER BY datetime(created_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_campaign_record(row) for row in rows]

    def get_campaign(self, campaign_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, job_id, name, industry, location, query, query_config_json, source, max_results, status,
                       total_leads, average_score, priority_leads, results_json, error_message,
                       created_at, started_at, completed_at, updated_at
                FROM campaigns
                WHERE id = ?
                """,
                (campaign_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_campaign_record(row)

    def get_campaign_by_job_id(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, job_id, name, industry, location, query, query_config_json, source, max_results, status,
                       total_leads, average_score, priority_leads, results_json, error_message,
                       created_at, started_at, completed_at, updated_at
                FROM campaigns
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_campaign_record(row)

    def upsert_source_session(
        self,
        *,
        source: str,
        cookies: dict[str, str],
        account_label: str | None,
        last_error: str | None = None,
    ) -> None:
        now = utc_now_iso()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO source_sessions (source, account_label, cookies_json, last_error, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(source) DO UPDATE SET
                    account_label = excluded.account_label,
                    cookies_json = excluded.cookies_json,
                    last_error = excluded.last_error,
                    updated_at = excluded.updated_at
                """,
                (
                    source,
                    account_label,
                    json.dumps(cookies),
                    last_error,
                    now,
                ),
            )

    def get_source_session(self, source: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT source, account_label, cookies_json, last_error, updated_at
                FROM source_sessions
                WHERE source = ?
                """,
                (source,),
            ).fetchone()
        if row is None:
            return None
        record = dict(row)
        record["cookies"] = json.loads(record.pop("cookies_json"))
        return record

    def delete_source_session(self, source: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("DELETE FROM source_sessions WHERE source = ?", (source,))

    def create_mailbox(
        self,
        *,
        mailbox_id: str,
        provider: str,
        email_address: str,
        note: str | None,
        imap_host: str,
        imap_port: int,
        smtp_host: str,
        smtp_port: int,
        smtp_starttls: bool,
        encrypted_auth_secret: str,
    ) -> None:
        now = utc_now_iso()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO mailboxes (
                    id, provider, email_address, note, imap_host, imap_port, smtp_host, smtp_port,
                    smtp_starttls, encrypted_auth_secret, status, last_error, last_synced_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mailbox_id,
                    provider,
                    email_address,
                    note,
                    imap_host,
                    imap_port,
                    smtp_host,
                    smtp_port,
                    1 if smtp_starttls else 0,
                    encrypted_auth_secret,
                    "ready",
                    None,
                    None,
                    now,
                    now,
                ),
            )

    def update_mailbox(
        self,
        mailbox_id: str,
        *,
        note: str | None,
        encrypted_auth_secret: str | None = None,
    ) -> None:
        fields: dict[str, Any] = {
            "note": note,
            "updated_at": utc_now_iso(),
        }
        if encrypted_auth_secret is not None:
            fields["encrypted_auth_secret"] = encrypted_auth_secret
        self._update_record("mailboxes", "id", mailbox_id, **fields)

    def mark_mailbox_ready(self, mailbox_id: str) -> None:
        now = utc_now_iso()
        self._update_record(
            "mailboxes",
            "id",
            mailbox_id,
            status="ready",
            last_error=None,
            last_synced_at=now,
            updated_at=now,
        )

    def mark_mailbox_error(self, mailbox_id: str, error_message: str) -> None:
        self._update_record(
            "mailboxes",
            "id",
            mailbox_id,
            status="error",
            last_error=error_message,
            updated_at=utc_now_iso(),
        )

    def list_mailboxes(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, provider, email_address, note, imap_host, imap_port, smtp_host, smtp_port,
                       smtp_starttls, encrypted_auth_secret, status, last_error, last_synced_at, created_at, updated_at
                FROM mailboxes
                ORDER BY datetime(created_at) DESC
                """
            ).fetchall()
        return [self._row_to_mailbox_record(row) for row in rows]

    def get_mailbox(self, mailbox_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, provider, email_address, note, imap_host, imap_port, smtp_host, smtp_port,
                       smtp_starttls, encrypted_auth_secret, status, last_error, last_synced_at, created_at, updated_at
                FROM mailboxes
                WHERE id = ?
                """,
                (mailbox_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_mailbox_record(row)

    def upsert_mail_message(
        self,
        *,
        message_id: str,
        mailbox_id: str,
        folder: str,
        remote_uid: str,
        message_id_header: str | None,
        subject: str,
        from_name: str | None,
        from_address: str | None,
        to_summary: str | None,
        snippet: str | None,
        body_text: str | None,
        is_read: bool,
        sent_at: str | None,
        received_at: str | None,
    ) -> None:
        now = utc_now_iso()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO mail_messages (
                    id, mailbox_id, folder, remote_uid, message_id_header, subject, from_name, from_address,
                    to_summary, snippet, body_text, is_read, sent_at, received_at, synced_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(mailbox_id, folder, remote_uid) DO UPDATE SET
                    message_id_header = excluded.message_id_header,
                    subject = excluded.subject,
                    from_name = excluded.from_name,
                    from_address = excluded.from_address,
                    to_summary = excluded.to_summary,
                    snippet = excluded.snippet,
                    body_text = excluded.body_text,
                    is_read = excluded.is_read,
                    sent_at = excluded.sent_at,
                    received_at = excluded.received_at,
                    synced_at = excluded.synced_at,
                    updated_at = excluded.updated_at
                """,
                (
                    message_id,
                    mailbox_id,
                    folder,
                    remote_uid,
                    message_id_header,
                    subject,
                    from_name,
                    from_address,
                    to_summary,
                    snippet,
                    body_text,
                    1 if is_read else 0,
                    sent_at,
                    received_at,
                    now,
                    now,
                    now,
                ),
            )

    def list_mail_messages(self, *, mailbox_id: str, folder: str, limit: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, mailbox_id, folder, remote_uid, message_id_header, subject, from_name, from_address,
                       to_summary, snippet, body_text, is_read, sent_at, received_at, synced_at, created_at, updated_at
                FROM mail_messages
                WHERE mailbox_id = ? AND folder = ?
                ORDER BY COALESCE(datetime(received_at), datetime(sent_at), datetime(created_at)) DESC
                LIMIT ?
                """,
                (mailbox_id, folder, limit),
            ).fetchall()
        return [self._row_to_mail_message_record(row) for row in rows]

    def get_mail_message(self, message_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, mailbox_id, folder, remote_uid, message_id_header, subject, from_name, from_address,
                       to_summary, snippet, body_text, is_read, sent_at, received_at, synced_at, created_at, updated_at
                FROM mail_messages
                WHERE id = ?
                """,
                (message_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_mail_message_record(row)

    def list_lead_recipients(self, *, limit: int) -> list[dict[str, Any]]:
        recipients: list[dict[str, Any]] = []
        seen: set[str] = set()
        for campaign in self.list_campaigns(limit=200):
            for lead in campaign["results"]:
                if not lead.email:
                    continue
                normalized = lead.email.casefold()
                if normalized in seen:
                    continue
                seen.add(normalized)
                recipients.append(
                    {
                        "id": f'{campaign["id"]}:{lead.email}',
                        "email": lead.email,
                        "lead_name": lead.name,
                        "campaign_id": campaign["id"],
                        "campaign_name": campaign["name"],
                        "source": lead.source,
                        "company": lead.current_company or None,
                    }
                )
                if len(recipients) >= limit:
                    return recipients
        return recipients

    # ── LLM config CRUD ────────────────────────────────────────────────

    def create_llm_config(
        self,
        *,
        config_id: str,
        provider: str,
        display_name: str,
        model_name: str,
        base_url: str,
        encrypted_api_key: str,
        official_url: str | None,
        note: str | None,
    ) -> None:
        now = utc_now_iso()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO llm_configs (
                    id, provider, display_name, model_name, base_url, official_url, note,
                    encrypted_api_key, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    config_id, provider, display_name, model_name, base_url,
                    official_url, note, encrypted_api_key, now, now,
                ),
            )

    def list_llm_configs(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, provider, display_name, model_name, base_url, official_url, note,
                       encrypted_api_key, is_active, created_at, updated_at
                FROM llm_configs
                ORDER BY datetime(created_at) DESC
                """
            ).fetchall()
        return [self._row_to_llm_config_record(row) for row in rows]

    def get_llm_config(self, config_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, provider, display_name, model_name, base_url, official_url, note,
                       encrypted_api_key, is_active, created_at, updated_at
                FROM llm_configs
                WHERE id = ?
                """,
                (config_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_llm_config_record(row)

    def update_llm_config(self, config_id: str, **fields: Any) -> None:
        fields["updated_at"] = utc_now_iso()
        self._update_record("llm_configs", "id", config_id, **fields)

    def delete_llm_config(self, config_id: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("DELETE FROM llm_configs WHERE id = ?", (config_id,))

    def activate_llm_config(self, config_id: str) -> None:
        now = utc_now_iso()
        with self._lock, self._connect() as connection:
            connection.execute("UPDATE llm_configs SET is_active = 0, updated_at = ?", (now,))
            connection.execute(
                "UPDATE llm_configs SET is_active = 1, updated_at = ? WHERE id = ?",
                (now, config_id),
            )

    def deactivate_llm_config(self, config_id: str) -> None:
        now = utc_now_iso()
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE llm_configs SET is_active = 0, updated_at = ? WHERE id = ?",
                (now, config_id),
            )

    def get_active_llm_config(self) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, provider, display_name, model_name, base_url, official_url, note,
                       encrypted_api_key, is_active, created_at, updated_at
                FROM llm_configs
                WHERE is_active = 1
                LIMIT 1
                """
            ).fetchone()
        if row is None:
            return None
        return self._row_to_llm_config_record(row)

    def _row_to_llm_config_record(self, row: sqlite3.Row) -> dict[str, Any]:
        record = dict(row)
        record["is_active"] = bool(record["is_active"])
        record["has_api_key"] = bool(record.get("encrypted_api_key"))
        return record

    # -- Sites CRUD --

    def create_site(
        self,
        *,
        site_id: str,
        display_name: str,
        slug: str,
        domain: str,
        server_ip: str,
        ssh_user: str,
        encrypted_ssh_password: str,
        wp_admin_user: str = "admin",
        encrypted_wp_admin_password: str | None = None,
        wp_admin_email: str = "",
        mysql_database: str,
        mysql_user: str,
        encrypted_mysql_password: str,
        encrypted_mysql_root_password: str,
        ssl_mode: str = "none",
        cloudflare_zone_id: str | None = None,
        encrypted_cloudflare_api_token: str | None = None,
        cloudflare_dns_proxy: bool = False,
        wp_plugins_json: str = "[]",
        note: str | None = None,
    ) -> None:
        now = utc_now_iso()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sites (
                    id, display_name, slug, domain, note,
                    server_ip, ssh_user, encrypted_ssh_password,
                    wp_admin_user, encrypted_wp_admin_password, wp_admin_email,
                    mysql_database, mysql_user, encrypted_mysql_password,
                    encrypted_mysql_root_password,
                    ssl_mode, cloudflare_zone_id, encrypted_cloudflare_api_token,
                    cloudflare_dns_proxy, wp_plugins_json,
                    status, created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?
                )
                """,
                (
                    site_id, display_name, slug, domain, note,
                    server_ip, ssh_user, encrypted_ssh_password,
                    wp_admin_user, encrypted_wp_admin_password, wp_admin_email,
                    mysql_database, mysql_user, encrypted_mysql_password,
                    encrypted_mysql_root_password,
                    ssl_mode, cloudflare_zone_id, encrypted_cloudflare_api_token,
                    int(cloudflare_dns_proxy), wp_plugins_json,
                    "draft", now, now,
                ),
            )

    def list_sites(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM sites ORDER BY datetime(created_at) DESC"
            ).fetchall()
        return [self._row_to_site_record(row) for row in rows]

    def get_site(self, site_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM sites WHERE id = ?", (site_id,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_site_record(row)

    def update_site(self, site_id: str, **fields: Any) -> None:
        fields["updated_at"] = utc_now_iso()
        self._update_record("sites", "id", site_id, **fields)

    def delete_site(self, site_id: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("DELETE FROM site_deployments WHERE site_id = ?", (site_id,))
            connection.execute("DELETE FROM sites WHERE id = ?", (site_id,))

    def _row_to_site_record(self, row: sqlite3.Row) -> dict[str, Any]:
        record = dict(row)
        record["has_ssh_password"] = bool(record.get("encrypted_ssh_password"))
        record["has_wp_admin_password"] = bool(record.get("encrypted_wp_admin_password"))
        record["has_mysql_password"] = bool(record.get("encrypted_mysql_password"))
        record["has_cloudflare_api_token"] = bool(record.get("encrypted_cloudflare_api_token"))
        record["cloudflare_dns_proxy"] = bool(record["cloudflare_dns_proxy"])
        record["wp_plugins"] = json.loads(record.pop("wp_plugins_json"))
        return record

    # -- Site Deployments CRUD --

    def create_deployment(
        self,
        *,
        deployment_id: str,
        site_id: str,
    ) -> None:
        now = utc_now_iso()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO site_deployments (id, site_id, status, log, created_at)
                VALUES (?, ?, 'pending', NULL, ?)
                """,
                (deployment_id, site_id, now),
            )

    def get_deployment(self, deployment_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM site_deployments WHERE id = ?", (deployment_id,)
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    def list_deployments_by_site(self, site_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM site_deployments
                WHERE site_id = ?
                ORDER BY datetime(created_at) DESC
                """,
                (site_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def update_deployment(self, deployment_id: str, **fields: Any) -> None:
        self._update_record("site_deployments", "id", deployment_id, **fields)

    def _update_record(self, table: str, key_column: str, key_value: str, **fields: Any) -> None:
        assignments = ", ".join(f"{column} = ?" for column in fields)
        values = list(fields.values())
        values.append(key_value)
        with self._lock, self._connect() as connection:
            connection.execute(
                f"UPDATE {table} SET {assignments} WHERE {key_column} = ?",
                values,
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_column(self, connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        existing_columns = {
            row["name"]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in existing_columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def _row_to_job_record(self, row: sqlite3.Row) -> dict[str, Any]:
        record = dict(row)
        record["query_config"] = json.loads(record.pop("query_config_json"))
        record["results"] = [
            ScrapedLead.model_validate(item)
            for item in json.loads(record.pop("results_json"))
        ]
        return record

    def _row_to_campaign_record(self, row: sqlite3.Row) -> dict[str, Any]:
        record = dict(row)
        record["query_config"] = json.loads(record.pop("query_config_json"))
        record["results"] = [
            EnrichedLead.model_validate(item)
            for item in json.loads(record.pop("results_json"))
        ]
        return record

    def _row_to_mailbox_record(self, row: sqlite3.Row) -> dict[str, Any]:
        record = dict(row)
        record["smtp_starttls"] = bool(record["smtp_starttls"])
        return record

    def _row_to_mail_message_record(self, row: sqlite3.Row) -> dict[str, Any]:
        record = dict(row)
        record["message_id"] = record.pop("message_id_header")
        record["is_read"] = bool(record["is_read"])
        return record
