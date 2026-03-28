from __future__ import annotations

from fastapi import Request

from app.core.database import Database
from app.core.job_manager import ScrapeJobManager
from app.services.llm.service import LlmConfigService
from app.services.mail.service import MailService
from app.services.scraping.linkedin_session import LinkedInSessionService
from app.services.sites.service import SitesService


def get_database(request: Request) -> Database:
    return request.app.state.database


def get_job_manager(request: Request) -> ScrapeJobManager:
    return request.app.state.job_manager


def get_linkedin_session_service(request: Request) -> LinkedInSessionService:
    return request.app.state.linkedin_session_service


def get_llm_config_service(request: Request) -> LlmConfigService:
    return request.app.state.llm_config_service


def get_mail_service(request: Request) -> MailService:
    return request.app.state.mail_service


def get_sites_service(request: Request) -> SitesService:
    return request.app.state.sites_service
