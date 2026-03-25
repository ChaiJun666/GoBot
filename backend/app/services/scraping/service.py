from __future__ import annotations

from app.core.config import Settings
from app.schemas.lead import ScrapedLead
from app.services.scraping.providers.google_maps import GoogleMapsScrapeProvider


class ScrapeService:
    def __init__(self, *, settings: Settings) -> None:
        self._providers = {
            "google_maps": GoogleMapsScrapeProvider(settings=settings),
        }

    async def scrape(self, *, query: str, max_results: int, source: str) -> list[ScrapedLead]:
        provider = self._providers.get(source)
        if provider is None:
            raise ValueError(f"Unsupported scrape source: {source}")
        return await provider.scrape(query=query, max_results=max_results)
