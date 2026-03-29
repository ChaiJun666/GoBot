from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.deps import get_mail_service
from app.schemas.mail import (
    CreateMailboxRequest,
    LeadRecipientSummary,
    MailFolder,
    MailMessageCountResponse,
    MailMessageDetail,
    MailMessageSummary,
    MailProviderConfig,
    MailboxSummary,
    MailboxSyncResponse,
    SendMailRequest,
    SendMailResponse,
    UpdateMailboxRequest,
)

router = APIRouter(prefix="/mail", tags=["mail"])


@router.get("/providers", response_model=list[MailProviderConfig])
async def list_mail_providers(request: Request) -> list[MailProviderConfig]:
    return get_mail_service(request).list_providers()


@router.get("/mailboxes", response_model=list[MailboxSummary])
async def list_mailboxes(request: Request) -> list[MailboxSummary]:
    return get_mail_service(request).list_mailboxes()


@router.post("/mailboxes", response_model=MailboxSummary, status_code=status.HTTP_201_CREATED)
async def create_mailbox(payload: CreateMailboxRequest, request: Request) -> MailboxSummary:
    service = get_mail_service(request)
    try:
        return await asyncio.to_thread(service.create_mailbox, payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/mailboxes/{mailbox_id}", response_model=MailboxSummary)
async def update_mailbox(mailbox_id: str, payload: UpdateMailboxRequest, request: Request) -> MailboxSummary:
    service = get_mail_service(request)
    try:
        return service.update_mailbox(mailbox_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/mailboxes/{mailbox_id}/sync", response_model=MailboxSyncResponse)
async def sync_mailbox(
    mailbox_id: str,
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
) -> MailboxSyncResponse:
    service = get_mail_service(request)
    try:
        return await asyncio.to_thread(service.sync_mailbox, mailbox_id, limit=limit)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/mailboxes/{mailbox_id}/messages", response_model=list[MailMessageSummary])
async def list_mail_messages(
    mailbox_id: str,
    request: Request,
    folder: MailFolder = Query(default=MailFolder.INBOX),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[MailMessageSummary]:
    service = get_mail_service(request)
    try:
        return service.list_messages(mailbox_id, folder=folder, limit=limit, offset=offset)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/mailboxes/{mailbox_id}/messages/count", response_model=MailMessageCountResponse)
async def count_mail_messages(
    mailbox_id: str,
    request: Request,
    folder: MailFolder = Query(default=MailFolder.INBOX),
) -> MailMessageCountResponse:
    service = get_mail_service(request)
    try:
        count = service.count_messages(mailbox_id, folder=folder)
        return MailMessageCountResponse(folder=folder, count=count)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/messages/{message_id}", response_model=MailMessageDetail)
async def get_mail_message(message_id: str, request: Request) -> MailMessageDetail:
    service = get_mail_service(request)
    try:
        return service.get_message(message_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/send", response_model=SendMailResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_mail(payload: SendMailRequest, request: Request) -> SendMailResponse:
    service = get_mail_service(request)
    try:
        return await asyncio.to_thread(service.send_mail, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/lead-recipients", response_model=list[LeadRecipientSummary])
async def list_lead_recipients(
    request: Request,
    limit: int = Query(default=200, ge=1, le=500),
) -> list[LeadRecipientSummary]:
    return get_mail_service(request).list_lead_recipients(limit=limit)
