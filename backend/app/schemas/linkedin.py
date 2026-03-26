from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ConnectLinkedInSessionRequest(BaseModel):
    username: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=3, max_length=200)


class LinkedInSessionStatus(BaseModel):
    source: str = "linkedin"
    connected: bool
    account_label: str | None = None
    last_error: str | None = None
    updated_at: datetime | None = None
