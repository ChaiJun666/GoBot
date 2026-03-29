from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.deps import get_database, get_job_manager
from app.schemas.campaigns import (
    CampaignDetail,
    CampaignSummary,
    CreateCampaignRequest,
    CreateCampaignResponse,
    UpdateLeadRequest,
    UpdateLeadResponse,
)
from app.schemas.source_query import resolve_query_payload

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
    try:
        resolved_query, resolved_query_config = resolve_query_payload(
            source=payload.source,
            query=payload.query,
            query_config=payload.query_config,
            fallback_location=payload.location,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    database.create_job(
        job_id=job_id,
        campaign_id=campaign_id,
        query=resolved_query,
        query_config=resolved_query_config,
        source=payload.source.value,
        max_results=payload.max_results,
    )
    database.create_campaign(
        campaign_id=campaign_id,
        job_id=job_id,
        name=payload.name,
        industry=payload.industry,
        location=payload.location,
        query=resolved_query,
        query_config=resolved_query_config,
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


@router.post("/{campaign_id}/retry", response_model=CampaignSummary, status_code=status.HTTP_202_ACCEPTED)
async def retry_campaign(campaign_id: str, request: Request) -> CampaignSummary:
    database = get_database(request)
    job_manager = get_job_manager(request)
    campaign = database.get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    if campaign["status"] != "failed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only failed campaigns can be retried")

    database.retry_campaign(campaign_id)
    database.retry_job(campaign["job_id"])
    await job_manager.enqueue(campaign["job_id"])

    refreshed = database.get_campaign(campaign_id)
    if refreshed is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retry campaign")
    return CampaignSummary.from_record(refreshed)


@router.get("/{campaign_id}", response_model=CampaignDetail)
async def get_campaign(campaign_id: str, request: Request) -> CampaignDetail:
    database = get_database(request)
    campaign = database.get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return CampaignDetail.from_record(campaign)


@router.patch("/{campaign_id}/leads/{lead_id}", response_model=UpdateLeadResponse)
async def update_campaign_lead(
    campaign_id: str,
    lead_id: str,
    payload: UpdateLeadRequest,
    request: Request,
) -> UpdateLeadResponse:
    database = get_database(request)
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    lead = database.update_campaign_lead(campaign_id, lead_id, updates)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign or lead not found")
    refreshed = database.get_campaign(campaign_id)
    return UpdateLeadResponse(
        lead=lead,
        campaign=CampaignSummary.from_record(refreshed),
    )


@router.delete("/{campaign_id}/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign_lead(
    campaign_id: str,
    lead_id: str,
    request: Request,
) -> None:
    database = get_database(request)
    deleted = database.delete_campaign_lead(campaign_id, lead_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign or lead not found")
