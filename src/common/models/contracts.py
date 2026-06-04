from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    event_id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RawEmailReceived(EventBase):
    event_type: str = "raw.email.received"
    email_id: UUID
    message_id: str
    source: str
    sender: str
    recipients: list[str]
    received_at: datetime
    subject: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    headers: Optional[dict[str, Any]] = None


class EmailParsed(EventBase):
    event_type: str = "email.parsed"
    email_id: UUID
    message_id: str
    subject: Optional[str] = None
    sender: str
    recipients: list[str]
    has_attachments: bool = False
    attachment_count: int = 0
    body_preview: Optional[str] = None


class EmailClassified(EventBase):
    event_type: str = "email.classified"
    email_id: UUID
    message_id: str
    category: str
    confidence: float = 0.0
    labels: list[str] = Field(default_factory=list)


class RecordExtracted(EventBase):
    event_type: str = "record.extracted"
    record_id: UUID
    email_id: UUID
    record_type: str
    data: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0


class RecordPersisted(EventBase):
    event_type: str = "record.persisted"
    record_id: UUID
    email_id: UUID
    record_type: str
    target_table: str
    persisted_at: datetime = Field(default_factory=datetime.utcnow)


class MatchFound(EventBase):
    event_type: str = "match.found"
    opportunity_id: UUID
    record_id: UUID
    matched_entity_id: UUID
    confidence: float = 0.0
    match_type: str
