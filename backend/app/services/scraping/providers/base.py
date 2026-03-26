from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from app.schemas.lead import ScrapedLead


class ScrapeProvider(ABC):
    source: str

    @abstractmethod
    async def scrape(
        self,
        *,
        query: str,
        max_results: int,
        query_config: Mapping[str, Any] | None = None,
    ) -> list[ScrapedLead]:
        raise NotImplementedError
