from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.schemas.llm import (
    ActiveLlmConfig,
    CreateLlmConfigRequest,
    LlmConfigSummary,
    LlmProviderPreset,
    UpdateLlmConfigRequest,
)
from app.services.llm.service import LlmConfigService

router = APIRouter(prefix="/llm", tags=["llm"])


def _get_service(request: Request) -> LlmConfigService:
    return request.app.state.llm_config_service


@router.get("/providers", response_model=list[LlmProviderPreset])
async def list_providers(request: Request) -> list[LlmProviderPreset]:
    return _get_service(request).get_provider_presets()


@router.get("/configs", response_model=list[LlmConfigSummary])
async def list_configs(request: Request) -> list[LlmConfigSummary]:
    return _get_service(request).list_configs()


@router.post("/configs", response_model=LlmConfigSummary, status_code=status.HTTP_201_CREATED)
async def create_config(payload: CreateLlmConfigRequest, request: Request) -> LlmConfigSummary:
    try:
        return _get_service(request).create_config(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/configs/active", response_model=ActiveLlmConfig | None)
async def get_active_config(request: Request) -> ActiveLlmConfig | None:
    return _get_service(request).get_active_config()


@router.get("/configs/{config_id}", response_model=LlmConfigSummary)
async def get_config(config_id: str, request: Request) -> LlmConfigSummary:
    try:
        return _get_service(request).get_config(config_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/configs/{config_id}", response_model=LlmConfigSummary)
async def update_config(config_id: str, payload: UpdateLlmConfigRequest, request: Request) -> LlmConfigSummary:
    try:
        return _get_service(request).update_config(config_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(config_id: str, request: Request) -> None:
    try:
        _get_service(request).delete_config(config_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/configs/{config_id}/activate", response_model=LlmConfigSummary)
async def activate_config(config_id: str, request: Request) -> LlmConfigSummary:
    try:
        return _get_service(request).activate_config(config_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
