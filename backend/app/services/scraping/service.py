from __future__ import annotations

from typing import Any, Mapping

from app.core.config import Settings
from app.schemas.lead import ScrapedLead
from app.services.scraping.providers.google_maps import GoogleMapsScrapeProvider
from app.services.scraping.providers.linkedin import LinkedInScrapeProvider
from app.services.scraping.linkedin_session import LinkedInSessionService


class ScrapeService:
    def __init__(self, *, settings: Settings, linkedin_session_service: LinkedInSessionService) -> None:
        self._providers = {
            "google_maps": GoogleMapsScrapeProvider(settings=settings),
            "linkedin": LinkedInScrapeProvider(
                settings=settings,
                session_service=linkedin_session_service,
            ),
        }

    async def scrape(
        self,
        *,
        query: str,
        max_results: int,
        source: str,
        query_config: Mapping[str, Any] | None = None,
    ) -> list[ScrapedLead]:
        provider = self._providers.get(source)
        if provider is None:
            raise ValueError(f"Unsupported scrape source: {source}")
        return await provider.scrape(query=query, max_results=max_results, query_config=query_config)
