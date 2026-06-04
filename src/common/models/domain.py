from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EmailData(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    message_id: str
    subject: Optional[str] = None
    sender: str
    recipients: list[str] = Field(default_factory=list)
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    received_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = "smtp"
    status: str = "received"
    checksum: Optional[str] = None
    headers: Optional[dict] = None


class AttachmentData(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    email_id: UUID
    filename: str
    content_type: str = "application/octet-stream"
    size: int = 0
    storage_path: Optional[str] = None
    storage_bucket: str = "shipping-attachments"


class ShippingRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    email_id: UUID
    record_type: str
    data: dict = Field(default_factory=dict)
    confidence: float = 0.0


class MatchResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    record_type: str
    source_id: UUID
    target_id: UUID
    confidence: float = 0.0
    status: str = "pending"
