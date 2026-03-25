from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.deps import get_database, get_job_manager
from app.schemas.campaigns import (
    CampaignDetail,
    CampaignSummary,
    CreateCampaignRequest,
    CreateCampaignResponse,
)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("", response_model=CreateCampaignResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_campaign(
    payload: CreateCampaignRequest,
    request: Request,
) -> CreateCampaignResponse:
    database = get_database(request)
    job_manager = get_job_manager(request)

    campaign_id = str(uuid4())
    job_id = str(uuid4())

    database.create_job(
        job_id=job_id,
        campaign_id=campaign_id,
        query=payload.query,
        source=payload.source.value,
        max_results=payload.max_results,
    )
    database.create_campaign(
        campaign_id=campaign_id,
        job_id=job_id,
        name=payload.name,
        industry=payload.industry,
        location=payload.location,
        query=payload.query,
        source=payload.source.value,
        max_results=payload.max_results,
    )
    await job_manager.enqueue(job_id)

    campaign = database.get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create campaign")

    return CreateCampaignResponse(campaign=CampaignSummary.from_record(campaign))


@router.get("", response_model=list[CampaignSummary])
async def list_campaigns(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[CampaignSummary]:
    database = get_database(request)
    return [CampaignSummary.from_record(item) for item in database.list_campaigns(limit=limit)]


@router.get("/{campaign_id}", response_model=CampaignDetail)
async def get_campaign(campaign_id: str, request: Request) -> CampaignDetail:
    database = get_database(request)
    campaign = database.get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return CampaignDetail.from_record(campaign)
