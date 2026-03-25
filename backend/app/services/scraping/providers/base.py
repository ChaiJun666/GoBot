from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.lead import ScrapedLead


class ScrapeProvider(ABC):
    source: str

    @abstractmethod
    async def scrape(self, *, query: str, max_results: int) -> list[ScrapedLead]:
        raise NotImplementedError
