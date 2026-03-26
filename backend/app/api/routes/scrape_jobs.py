from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.deps import get_database, get_job_manager
from app.schemas.scrape_jobs import (
    CreateScrapeJobRequest,
    CreateScrapeJobResponse,
    ScrapeJobResultsResponse,
    ScrapeJobSummary,
)

router = APIRouter(prefix="/scrape-jobs", tags=["scrape-jobs"])


@router.post("", response_model=CreateScrapeJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_scrape_job(
    payload: CreateScrapeJobRequest,
    request: Request,
) -> CreateScrapeJobResponse:
    database = get_database(request)
    job_manager = get_job_manager(request)
    job_id = str(uuid4())

    database.create_job(
        job_id=job_id,
        query=payload.query,
        source=payload.source.value,
        max_results=payload.max_results,
    )
    await job_manager.enqueue(job_id)

    job = database.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create job")

    return CreateScrapeJobResponse(job=ScrapeJobSummary.from_record(job))


@router.get("", response_model=list[ScrapeJobSummary])
async def list_scrape_jobs(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ScrapeJobSummary]:
    database = get_database(request)
    return [ScrapeJobSummary.from_record(job) for job in database.list_jobs(limit=limit)]


@router.get("/{job_id}", response_model=ScrapeJobSummary)
async def get_scrape_job(job_id: str, request: Request) -> ScrapeJobSummary:
    database = get_database(request)
    job = database.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return ScrapeJobSummary.from_record(job)


@router.post("/{job_id}/retry", response_model=ScrapeJobSummary, status_code=status.HTTP_202_ACCEPTED)
async def retry_scrape_job(job_id: str, request: Request) -> ScrapeJobSummary:
    database = get_database(request)
    job_manager = get_job_manager(request)
    job = database.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job["status"] != "failed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only failed jobs can be retried")

    database.retry_job(job_id)
    campaign = database.get_campaign_by_job_id(job_id)
    if campaign is not None:
        database.retry_campaign(campaign["id"])

    await job_manager.enqueue(job_id)

    refreshed = database.get_job(job_id)
    if refreshed is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retry job")
    return ScrapeJobSummary.from_record(refreshed)


@router.get("/{job_id}/results", response_model=ScrapeJobResultsResponse)
async def get_scrape_job_results(job_id: str, request: Request) -> ScrapeJobResultsResponse:
    database = get_database(request)
    job = database.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return ScrapeJobResultsResponse(
        job=ScrapeJobSummary.from_record(job),
        results=job["results"],
    )
