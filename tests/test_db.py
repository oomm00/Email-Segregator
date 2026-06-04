import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.db.base import Base
from src.common.db.models import (
    RawEmail,
    EmailAttachment,
    DedupFingerprint,
    AuditLog,
    User,
    Account,
    Port,
    MatchOpportunity,
)


@pytest.mark.asyncio
async def test_db_connection(db_session: AsyncSession):
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_tables_defined():
    tables = Base.metadata.tables
    assert "raw_emails" in tables
    assert "email_attachments" in tables
    assert "dedup_fingerprints" in tables
    assert "audit_logs" in tables
    assert "users" in tables
    assert "accounts" in tables
    assert "ports" in tables
    assert "match_opportunities" in tables


def test_raw_email_columns():
    cols = RawEmail.__table__.columns
    assert "id" in cols
    assert "message_id" in cols
    assert "subject" in cols
    assert "sender" in cols
    assert "body_text" in cols
    assert "received_at" in cols
    assert "status" in cols
    assert "checksum" in cols
    assert "is_deleted" in cols


def test_raw_email_has_relationships():
    assert hasattr(RawEmail, "attachments")


def test_model_table_names():
    assert RawEmail.__tablename__ == "raw_emails"
    assert EmailAttachment.__tablename__ == "email_attachments"
    assert DedupFingerprint.__tablename__ == "dedup_fingerprints"
    assert AuditLog.__tablename__ == "audit_logs"
    assert User.__tablename__ == "users"
    assert Account.__tablename__ == "accounts"
    assert Port.__tablename__ == "ports"
    assert MatchOpportunity.__tablename__ == "match_opportunities"
