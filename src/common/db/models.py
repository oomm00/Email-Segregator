from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.db.base import Base, TimestampMixin, SoftDeleteMixin


class RawEmail(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "raw_emails"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=None)
    message_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[Optional[str]] = mapped_column(String(1024))
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    recipients: Mapped[Optional[str]] = mapped_column(Text)
    body_text: Mapped[Optional[str]] = mapped_column(Text)
    body_html: Mapped[Optional[str]] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="smtp")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="received", index=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(64))
    headers: Mapped[Optional[dict]] = mapped_column(JSONB)

    attachments = relationship("EmailAttachment", back_populates="email", lazy="selectin")

    __table_args__ = (
        Index("idx_raw_emails_received_at", "received_at"),
        Index("idx_raw_emails_sender", "sender"),
        Index("idx_raw_emails_checksum", "checksum"),
    )


class EmailAttachment(TimestampMixin, Base):
    __tablename__ = "email_attachments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=None)
    email_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("raw_emails.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False, default="application/octet-stream")
    size: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(255), nullable=False, default="shipping-attachments")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    email = relationship("RawEmail", back_populates="attachments")

    __table_args__ = (
        Index("idx_email_attachments_email_id", "email_id"),
    )


class DedupFingerprint(Base):
    __tablename__ = "dedup_fingerprints"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=None)
    fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    message_id: Mapped[str] = mapped_column(String(255), nullable=False)
    email_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("raw_emails.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=None
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=None)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=None
    )

    __table_args__ = (
        Index("idx_audit_logs_entity", "entity_type", "entity_id"),
        Index("idx_audit_logs_created_at", "created_at"),
    )


class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=None)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("idx_users_email_active", "email", "is_active"),
    )


class Account(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "accounts"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=None)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        Index("idx_accounts_code", "code"),
        Index("idx_accounts_name", "name"),
    )


class Port(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "ports"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=None)
    code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(100))

    __table_args__ = (
        Index("idx_ports_code", "code"),
        Index("idx_ports_country", "country"),
    )


class MatchOpportunity(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "match_opportunities"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=None)
    record_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    target_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    matched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_match_opp_status", "status"),
        Index("idx_match_opp_record_type", "record_type"),
        Index("idx_match_opp_source_target", "source_id", "target_id"),
    )
