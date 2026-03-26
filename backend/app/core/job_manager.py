from __future__ import annotations

import asyncio

from app.core.database import Database
from app.services.intelligence.scoring import LeadIntelligenceScorer
from app.services.scraping.service import ScrapeService


class ScrapeJobManager:
    def __init__(
        self,
        *,
        database: Database,
        scrape_service: ScrapeService,
        intelligence_scorer: LeadIntelligenceScorer,
    ) -> None:
        self.database = database
        self.scrape_service = scrape_service
        self.intelligence_scorer = intelligence_scorer
        self._tasks: dict[str, asyncio.Task[None]] = {}

    async def enqueue(self, job_id: str) -> None:
        if job_id in self._tasks:
            return
        self._tasks[job_id] = asyncio.create_task(self._run(job_id))

    async def shutdown(self) -> None:
        if not self._tasks:
            return
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()

    async def _run(self, job_id: str) -> None:
        try:
            job = self.database.get_job(job_id)
            if job is None:
                return

            campaign = self.database.get_campaign_by_job_id(job_id)
            self.database.mark_job_running(job_id)
            if campaign is not None:
                self.database.mark_campaign_running(campaign["id"])
            results = await self.scrape_service.scrape(
                query=job["query"],
                max_results=job["max_results"],
                source=job["source"],
                query_config=job.get("query_config"),
            )
            self.database.complete_job(job_id, results)
            if campaign is not None:
                enriched_results = self.intelligence_scorer.score_leads(
                    results,
                    industry=campaign["industry"],
                )
                summary = self.intelligence_scorer.summarize(enriched_results)
                self.database.complete_campaign(
                    campaign["id"],
                    enriched_results,
                    total_leads=summary["total_leads"],
                    average_score=summary["average_score"],
                    priority_leads=summary["priority_leads"],
                )
        except asyncio.CancelledError:
            self.database.fail_job(job_id, "Job cancelled during shutdown")
            campaign = self.database.get_campaign_by_job_id(job_id)
            if campaign is not None:
                self.database.fail_campaign(campaign["id"], "Campaign cancelled during shutdown")
            raise
        except Exception as exc:  # pragma: no cover - defensive path
            self.database.fail_job(job_id, str(exc))
            campaign = self.database.get_campaign_by_job_id(job_id)
            if campaign is not None:
                self.database.fail_campaign(campaign["id"], str(exc))
        finally:
            self._tasks.pop(job_id, None)
