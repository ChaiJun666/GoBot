from __future__ import annotations

from fastapi import Request

from app.core.database import Database
from app.core.job_manager import ScrapeJobManager


def get_database(request: Request) -> Database:
    return request.app.state.database


def get_job_manager(request: Request) -> ScrapeJobManager:
    return request.app.state.job_manager
