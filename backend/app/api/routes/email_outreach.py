from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.deps import get_email_generator_service
from app.schemas.email_outreach import (
    GenerateEmailsRequest,
    GenerateEmailsResponse,
    LeadOutreachSummary,
    SendEmailsRequest,
    SendEmailsResponse,
    UpdateLeadStageRequest,
)

router = APIRouter(prefix="/email-outreach", tags=["email-outreach"])


@router.get("/leads", response_model=list[LeadOutreachSummary])
async def list_outreach_leads(
    request: Request,
    campaign_id: str | None = Query(default=None),
    stage: int | None = Query(default=None, ge=1, le=5),
) -> list[LeadOutreachSummary]:
    service = get_email_generator_service(request)
    return service.list_outreach_leads(campaign_id=campaign_id, stage=stage)


@router.patch("/leads/{lead_id}/stage", response_model=LeadOutreachSummary)
async def update_lead_stage(
    lead_id: str,
    payload: UpdateLeadStageRequest,
    request: Request,
) -> LeadOutreachSummary:
    service = get_email_generator_service(request)
    try:
        return service.update_lead_stage(lead_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/generate", response_model=GenerateEmailsResponse)
async def generate_emails(
    payload: GenerateEmailsRequest,
    request: Request,
) -> GenerateEmailsResponse:
    service = get_email_generator_service(request)
    try:
        return await service.generate_emails(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/send", response_model=SendEmailsResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_emails(
    payload: SendEmailsRequest,
    request: Request,
) -> SendEmailsResponse:
    service = get_email_generator_service(request)
    return service.send_emails(payload.emails)


@router.get("/history/{lead_id}")
async def get_lead_email_history(lead_id: str, request: Request) -> dict:
    service = get_email_generator_service(request)
    try:
        return service.get_lead_history(lead_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/campaigns/{campaign_id}/init-stages")
async def init_campaign_lead_stages(campaign_id: str, request: Request) -> dict:
    service = get_email_generator_service(request)
    try:
        created = service.ensure_lead_stages_for_campaign(campaign_id)
        return {"campaign_id": campaign_id, "leads_initialized": created}
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
