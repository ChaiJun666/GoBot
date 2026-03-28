from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.schemas.site import (
    CreateSiteRequest,
    DeploySiteResponse,
    SiteDeployment,
    SiteSummary,
    UpdateSiteRequest,
)
from app.services.sites.service import SitesService

router = APIRouter(prefix="/sites", tags=["sites"])


def _get_service(request: Request) -> SitesService:
    return request.app.state.sites_service


@router.get("", response_model=list[SiteSummary])
async def list_sites(request: Request) -> list[SiteSummary]:
    return _get_service(request).list_sites()


@router.post("", response_model=SiteSummary, status_code=status.HTTP_201_CREATED)
async def create_site(payload: CreateSiteRequest, request: Request) -> SiteSummary:
    try:
        return _get_service(request).create_site(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{site_id}", response_model=SiteSummary)
async def get_site(site_id: str, request: Request) -> SiteSummary:
    try:
        return _get_service(request).get_site(site_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/{site_id}", response_model=SiteSummary)
async def update_site(site_id: str, payload: UpdateSiteRequest, request: Request) -> SiteSummary:
    try:
        return _get_service(request).update_site(site_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(site_id: str, request: Request) -> None:
    try:
        _get_service(request).delete_site(site_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{site_id}/deploy", response_model=DeploySiteResponse, status_code=status.HTTP_202_ACCEPTED)
async def deploy_site(site_id: str, request: Request) -> DeploySiteResponse:
    try:
        return await _get_service(request).deploy_site(site_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{site_id}/deployments", response_model=list[SiteDeployment])
async def list_deployments(site_id: str, request: Request) -> list[SiteDeployment]:
    return _get_service(request).list_deployments(site_id)
