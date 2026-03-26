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
