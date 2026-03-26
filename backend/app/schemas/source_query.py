from __future__ import annotations

from typing import Any, Mapping

from pydantic import BaseModel, Field

from app.schemas.scrape_jobs import ScrapeSource


class GoogleMapsQueryConfig(BaseModel):
    query: str = Field(min_length=2, max_length=200)


class LinkedInPersonQueryConfig(BaseModel):
    keywords: str = Field(min_length=2, max_length=120)
    title: str | None = Field(default=None, max_length=120)
    company: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=120)


def resolve_query_payload(
    *,
    source: ScrapeSource,
    query: str | None,
    query_config: Mapping[str, Any] | None,
    fallback_location: str | None = None,
) -> tuple[str, dict[str, Any]]:
    if source is ScrapeSource.GOOGLE_MAPS:
        config = GoogleMapsQueryConfig.model_validate(query_config or {"query": query})
        return config.query, config.model_dump(mode="json")

    if source is ScrapeSource.LINKEDIN:
        payload = dict(query_config or {})
        if fallback_location and not payload.get("location"):
            payload["location"] = fallback_location
        config = LinkedInPersonQueryConfig.model_validate(payload)
        summary = " | ".join(
            value
            for value in (config.keywords, config.title, config.company, config.location)
            if value
        )
        return summary, config.model_dump(mode="json")

    raise ValueError(f"Unsupported source: {source}")
