from __future__ import annotations

from fastapi import APIRouter, Request, status

from app.api.deps import get_linkedin_session_service
from app.schemas.linkedin import ConnectLinkedInSessionRequest, LinkedInSessionStatus

router = APIRouter(prefix="/linkedin", tags=["linkedin"])


@router.get("/session", response_model=LinkedInSessionStatus)
async def get_linkedin_session(request: Request) -> LinkedInSessionStatus:
    session_service = get_linkedin_session_service(request)
    return await session_service.get_status()


@router.post("/session", response_model=LinkedInSessionStatus, status_code=status.HTTP_202_ACCEPTED)
async def connect_linkedin_session(
    payload: ConnectLinkedInSessionRequest,
    request: Request,
) -> LinkedInSessionStatus:
    session_service = get_linkedin_session_service(request)
    return await session_service.connect(username=payload.username, password=payload.password)


@router.delete("/session", response_model=LinkedInSessionStatus)
async def disconnect_linkedin_session(request: Request) -> LinkedInSessionStatus:
    session_service = get_linkedin_session_service(request)
    return await session_service.disconnect()
