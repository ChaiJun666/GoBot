from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.deps import get_database

router = APIRouter(tags=["health"])


@router.get("/health")
async def healthcheck(request: Request) -> dict[str, object]:
    database = get_database(request)
    settings = request.app.state.settings
    return {
        "status": "ok",
        "database": {
            "path": str(settings.resolved_database_path),
            "healthy": database.healthcheck(),
        },
        "scraper": {
            "headless": settings.scraper_headless,
            "timeout_ms": settings.scraper_timeout_ms,
        },
    }
