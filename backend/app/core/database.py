from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import sqlite3
import threading
from typing import Any

from app.schemas.lead import ScrapedLead


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
                    query TEXT NOT NULL,
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
                """
            )

    def healthcheck(self) -> bool:
        try:
            with self._connect() as connection:
                connection.execute("SELECT 1")
            return True
        except sqlite3.Error:
            return False

    def create_job(self, *, job_id: str, query: str, source: str, max_results: int) -> None:
        now = utc_now_iso()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scrape_jobs (
                    id, query, source, max_results, status, result_count, results_json,
                    error_message, created_at, started_at, completed_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    query,
                    source,
                    max_results,
                    "queued",
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
        self._update_job(
            job_id,
            status="running",
            started_at=now,
            updated_at=now,
            error_message=None,
        )

    def complete_job(self, job_id: str, results: list[ScrapedLead]) -> None:
        now = utc_now_iso()
        self._update_job(
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
        self._update_job(
            job_id,
            status="failed",
            completed_at=now,
            updated_at=now,
            error_message=error_message,
        )

    def list_jobs(self, *, limit: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, query, source, max_results, status, result_count, results_json,
                       error_message, created_at, started_at, completed_at, updated_at
                FROM scrape_jobs
                ORDER BY datetime(created_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, query, source, max_results, status, result_count, results_json,
                       error_message, created_at, started_at, completed_at, updated_at
                FROM scrape_jobs
                WHERE id = ?
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def _update_job(self, job_id: str, **fields: Any) -> None:
        assignments = ", ".join(f"{column} = ?" for column in fields)
        values = list(fields.values())
        values.append(job_id)
        with self._lock, self._connect() as connection:
            connection.execute(
                f"UPDATE scrape_jobs SET {assignments} WHERE id = ?",
                values,
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _row_to_record(self, row: sqlite3.Row) -> dict[str, Any]:
        record = dict(row)
        record["results"] = [
            ScrapedLead.model_validate(item)
            for item in json.loads(record.pop("results_json"))
        ]
        return record
