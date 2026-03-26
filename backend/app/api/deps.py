from __future__ import annotations

from fastapi import Request

from app.core.database import Database
from app.core.job_manager import ScrapeJobManager
from app.services.scraping.linkedin_session import LinkedInSessionService


def get_database(request: Request) -> Database:
    return request.app.state.database


def get_job_manager(request: Request) -> ScrapeJobManager:
    return request.app.state.job_manager


def get_linkedin_session_service(request: Request) -> LinkedInSessionService:
    return request.app.state.linkedin_session_service
