from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
import uvicorn

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.database import Database
from app.core.job_manager import ScrapeJobManager
from app.services.intelligence.scoring import LeadIntelligenceScorer
from app.services.mail.crypto import MailSecretCipher
from app.services.mail.service import MailService
from app.services.scraping.linkedin_session import LinkedInSessionService
from app.services.scraping.service import ScrapeService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    database = Database(settings.resolved_database_path)
    database.initialize()
    mail_cipher = MailSecretCipher(settings.resolved_mail_secret_key_path)
    mail_service = MailService(database=database, cipher=mail_cipher)
    linkedin_session_service = LinkedInSessionService(settings=settings, database=database)
    scrape_service = ScrapeService(
        settings=settings,
        linkedin_session_service=linkedin_session_service,
    )
    intelligence_scorer = LeadIntelligenceScorer()
    job_manager = ScrapeJobManager(
        database=database,
        scrape_service=scrape_service,
        intelligence_scorer=intelligence_scorer,
    )

    app.state.settings = settings
    app.state.database = database
    app.state.job_manager = job_manager
    app.state.intelligence_scorer = intelligence_scorer
    app.state.linkedin_session_service = linkedin_session_service
    app.state.mail_service = mail_service

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
    register_frontend_routes(application, resolved_settings)

    return application


def register_frontend_routes(application: FastAPI, settings: Settings) -> None:
    dist_dir = settings.resolved_frontend_dist_path
    index_file = dist_dir / "index.html"

    @application.get("/", include_in_schema=False, response_model=None)
    async def root() -> Response:
        if settings.serve_frontend and index_file.exists():
            return FileResponse(index_file)
        return JSONResponse(
            {
                "name": settings.app_name,
                "docs": "/docs",
                "api_prefix": settings.api_prefix,
            }
        )

    @application.get("/{full_path:path}", include_in_schema=False, response_model=None)
    async def frontend_fallback(full_path: str) -> FileResponse:
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json")):
            raise HTTPException(status_code=404, detail="Not found")
        if not settings.serve_frontend or not index_file.exists():
            raise HTTPException(status_code=404, detail="Frontend build not found")

        candidate = dist_dir / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index_file)


app = create_app()


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=False,
    )
