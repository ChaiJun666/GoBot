from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class IntelligenceFactors(BaseModel):
    data_completeness: int
    business_quality: int
    digital_presence: int
    location_value: int
    industry_potential: int
    contactability: int


class LeadIntelligence(BaseModel):
    score: int
    category: str
    priority: str
    recommendation: str
    factors: IntelligenceFactors


class ScrapedLead(BaseModel):
    name: str
    address: str
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    reference_link: str | None = None
    rating: str | None = None
    has_website: bool = False
    source: str = "google_maps"
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EnrichedLead(ScrapedLead):
    intelligence: LeadIntelligence
