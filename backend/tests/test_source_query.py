from __future__ import annotations

from app.schemas.scrape_jobs import ScrapeSource
from app.schemas.source_query import resolve_query_payload


def test_resolve_query_payload_for_google_maps_uses_query_string() -> None:
    query, config = resolve_query_payload(
        source=ScrapeSource.GOOGLE_MAPS,
        query="coffee shops jakarta",
        query_config=None,
    )

    assert query == "coffee shops jakarta"
    assert config == {"query": "coffee shops jakarta"}


def test_resolve_query_payload_for_linkedin_builds_summary_and_location_fallback() -> None:
    query, config = resolve_query_payload(
        source=ScrapeSource.LINKEDIN,
        query=None,
        query_config={
            "keywords": "growth marketer",
            "title": "Head of Growth",
            "company": "OpenAI",
        },
        fallback_location="Singapore",
    )

    assert query == "growth marketer | Head of Growth | OpenAI | Singapore"
    assert config == {
      "keywords": "growth marketer",
      "title": "Head of Growth",
      "company": "OpenAI",
      "location": "Singapore",
    }
