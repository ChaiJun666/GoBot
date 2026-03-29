from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MailboxStatus(str, Enum):
    READY = "ready"
    ERROR = "error"


class MailFolder(str, Enum):
    INBOX = "inbox"
    SENT = "sent"


class MailProviderKey(str, Enum):
    NETEASE_163 = "163.com"
    NETEASE_163_VIP = "vip.163.com"
    NETEASE_126 = "126.com"
    NETEASE_126_VIP = "vip.126.com"
    NETEASE_188 = "188.com"
    NETEASE_188_VIP = "vip.188.com"
    YEAH = "yeah.net"
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    QQ = "qq"


class MailProviderConfig(BaseModel):
    key: MailProviderKey
    label: str
    imap_host: str
    imap_port: int
    smtp_host: str
    smtp_port: int
    smtp_starttls: bool


class CreateMailboxRequest(BaseModel):
    provider: MailProviderKey
    email_address: str = Field(min_length=3, max_length=255)
    auth_secret: str = Field(min_length=3, max_length=255)
    note: str | None = Field(default=None, max_length=120)


class UpdateMailboxRequest(BaseModel):
    note: str | None = Field(default=None, max_length=120)
    auth_secret: str | None = Field(default=None, min_length=3, max_length=255)


class MailboxSummary(BaseModel):
    id: str
    provider: MailProviderKey
    email_address: str
    note: str | None = None
    imap_host: str
    imap_port: int
    smtp_host: str
    smtp_port: int
    smtp_starttls: bool
    status: MailboxStatus
    last_error: str | None = None
    last_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_record(cls, record: dict[str, object]) -> "MailboxSummary":
        return cls.model_validate(record)


class MailMessageSummary(BaseModel):
    id: str
    mailbox_id: str
    folder: MailFolder
    remote_uid: str
    message_id: str | None = None
    subject: str
    from_name: str | None = None
    from_address: str | None = None
    to_summary: str | None = None
    snippet: str | None = None
    is_read: bool = False
    sent_at: datetime | None = None
    received_at: datetime | None = None
    synced_at: datetime

    @classmethod
    def from_record(cls, record: dict[str, object]) -> "MailMessageSummary":
        return cls.model_validate(record)


class MailMessageDetail(MailMessageSummary):
    body_text: str | None = None

    @classmethod
    def from_record(cls, record: dict[str, object]) -> "MailMessageDetail":
        return cls.model_validate(record)


class SendMailRequest(BaseModel):
    mailbox_id: str
    to: list[str] = Field(min_length=1)
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=20_000)


class SendMailResponse(BaseModel):
    mailbox: MailboxSummary
    accepted: list[str]
    message: str


class LeadRecipientSummary(BaseModel):
    id: str
    email: str
    lead_name: str
    campaign_id: str
    campaign_name: str
    source: str
    company: str | None = None


class MailboxSyncResponse(BaseModel):
    mailbox: MailboxSummary
    inbox_count: int = 0
    sent_count: int = 0


class MailMessageCountResponse(BaseModel):
    folder: MailFolder
    count: int
