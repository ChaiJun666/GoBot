from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.lead import ScrapedLead


class ScrapeSource(str, Enum):
    GOOGLE_MAPS = "google_maps"
    LINKEDIN = "linkedin"


class ScrapeJobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CreateScrapeJobRequest(BaseModel):
    query: str | None = Field(default=None, min_length=2, max_length=200)
    query_config: dict[str, Any] | None = None
    max_results: int = Field(default=20, ge=1, le=100)
    source: ScrapeSource = ScrapeSource.GOOGLE_MAPS


class ScrapeJobSummary(BaseModel):
    id: str
    campaign_id: str | None = None
    query: str
    query_config: dict[str, Any] | None = None
    source: ScrapeSource
    max_results: int
    status: ScrapeJobStatus
    result_count: int = 0
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "ScrapeJobSummary":
        return cls.model_validate(record)


class CreateScrapeJobResponse(BaseModel):
    job: ScrapeJobSummary


class ScrapeJobResultsResponse(BaseModel):
    job: ScrapeJobSummary
    results: list[ScrapedLead]
