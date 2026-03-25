from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.database import Database
from app.core.job_manager import ScrapeJobManager
from app.services.scraping.service import ScrapeService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    database = Database(settings.resolved_database_path)
    database.initialize()
    scrape_service = ScrapeService(settings=settings)
    job_manager = ScrapeJobManager(database=database, scrape_service=scrape_service)

    app.state.settings = settings
    app.state.database = database
    app.state.job_manager = job_manager

    yield

    await job_manager.shutdown()


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    application = FastAPI(
        title=resolved_settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    application.include_router(api_router, prefix=resolved_settings.api_prefix)

    @application.get("/", tags=["meta"])
    async def root() -> dict[str, str]:
        return {
            "name": resolved_settings.app_name,
            "docs": "/docs",
            "api_prefix": resolved_settings.api_prefix,
        }

    return application


app = create_app()


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=False,
    )
