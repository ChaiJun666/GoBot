from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.lead import EnrichedLead
from app.schemas.scrape_jobs import ScrapeSource


class CampaignStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CreateCampaignRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    industry: str = Field(min_length=2, max_length=40)
    location: str = Field(min_length=2, max_length=80)
    query: str | None = Field(default=None, min_length=2, max_length=200)
    query_config: dict[str, Any] | None = None
    max_results: int = Field(default=20, ge=1, le=100)
    source: ScrapeSource = ScrapeSource.GOOGLE_MAPS


class CampaignSummary(BaseModel):
    id: str
    job_id: str
    name: str
    industry: str
    location: str
    query: str
    query_config: dict[str, Any] | None = None
    source: ScrapeSource
    max_results: int
    status: CampaignStatus
    total_leads: int = 0
    average_score: int = 0
    priority_leads: int = 0
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "CampaignSummary":
        return cls.model_validate(record)


class CampaignDetail(CampaignSummary):
    results: list[EnrichedLead] = Field(default_factory=list)

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "CampaignDetail":
        return cls.model_validate(record)


class CreateCampaignResponse(BaseModel):
    campaign: CampaignSummary
