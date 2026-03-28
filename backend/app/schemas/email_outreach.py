from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OutreachStage(int, Enum):
    INITIAL_OUTREACH = 1
    INTEREST_CHECK = 2
    NEEDS_DISCOVERY = 3
    PROPOSAL = 4
    CLOSING = 5


OUTREACH_STAGE_LABELS: dict[OutreachStage, dict[str, str]] = {
    OutreachStage.INITIAL_OUTREACH: {"en": "Initial Outreach", "zh": "初次触达"},
    OutreachStage.INTEREST_CHECK: {"en": "Interest Check", "zh": "确认兴趣"},
    OutreachStage.NEEDS_DISCOVERY: {"en": "Needs Discovery", "zh": "需求探测"},
    OutreachStage.PROPOSAL: {"en": "Proposal", "zh": "方案推荐"},
    OutreachStage.CLOSING: {"en": "Closing", "zh": "成交跟进"},
}

OUTREACH_STAGE_FOLLOW_UP_DAYS: dict[OutreachStage, int] = {
    OutreachStage.INITIAL_OUTREACH: 0,
    OutreachStage.INTEREST_CHECK: 3,
    OutreachStage.NEEDS_DISCOVERY: 5,
    OutreachStage.PROPOSAL: 7,
    OutreachStage.CLOSING: 10,
}


class LeadOutreachSummary(BaseModel):
    id: str
    lead_id: str
    lead_email: str
    lead_name: str
    lead_company: str | None = None
    lead_industry: str | None = None
    lead_location: str | None = None
    lead_source: str | None = None
    lead_headline: str | None = None
    campaign_id: str
    campaign_name: str | None = None
    current_stage: int = 1
    emails_sent: int = 0
    last_email_at: datetime | None = None
    next_stage_at: datetime | None = None
    language: str = "auto"
    manual_override: bool = False
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_record(cls, record: dict) -> "LeadOutreachSummary":
        return cls.model_validate(record)


class UpdateLeadStageRequest(BaseModel):
    stage: int = Field(ge=1, le=5)
    manual_override: bool = True


class GenerateEmailsRequest(BaseModel):
    lead_ids: list[str] = Field(min_length=1, max_length=50)
    stage: int | None = Field(default=None, ge=1, le=5)
    language: str | None = Field(default=None, pattern=r"^(auto|en|zh)$")
    user_instructions: str | None = Field(default=None, max_length=1000)


class GeneratedEmail(BaseModel):
    lead_id: str
    subject: str
    body: str


class GenerateEmailsResponse(BaseModel):
    emails: list[GeneratedEmail]
    errors: list[dict] = Field(default_factory=list)


class SendEmailItem(BaseModel):
    lead_id: str
    mailbox_id: str
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=20000)


class SendEmailsRequest(BaseModel):
    emails: list[SendEmailItem] = Field(min_length=1, max_length=50)


class SendEmailResult(BaseModel):
    lead_id: str
    status: str = "sent"
    error: str | None = None


class SendEmailsResponse(BaseModel):
    results: list[SendEmailResult]


class LeadEmailHistory(BaseModel):
    lead_id: str
    lead_name: str
    messages: list[dict] = Field(default_factory=list)
