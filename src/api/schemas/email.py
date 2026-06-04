from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InboundEmailRequest(BaseModel):
    message_id: str
    sender: str
    recipients: list[str] = Field(default_factory=list)
    subject: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    received_at: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[str] = "smtp"
    headers: Optional[dict] = None


class InboundEmailResponse(BaseModel):
    email_id: UUID
    status: str
    correlation_id: Optional[str] = None


class AdminUploadResponse(BaseModel):
    email_id: UUID
    filename: str
    size: int
    status: str
