from __future__ import annotations

import asyncio

from app.core.database import Database
from app.services.scraping.service import ScrapeService


class ScrapeJobManager:
    def __init__(self, *, database: Database, scrape_service: ScrapeService) -> None:
        self.database = database
        self.scrape_service = scrape_service
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

            self.database.mark_job_running(job_id)
            results = await self.scrape_service.scrape(
                query=job["query"],
                max_results=job["max_results"],
                source=job["source"],
            )
            self.database.complete_job(job_id, results)
        except asyncio.CancelledError:
            self.database.fail_job(job_id, "Job cancelled during shutdown")
            raise
        except Exception as exc:  # pragma: no cover - defensive path
            self.database.fail_job(job_id, str(exc))
        finally:
            self._tasks.pop(job_id, None)
