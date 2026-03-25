from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ScrapedLead(BaseModel):
    name: str
    address: str
    phone: str | None = None
    website: str | None = None
    reference_link: str | None = None
    rating: str | None = None
    has_website: bool = False
    source: str = "google_maps"
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
