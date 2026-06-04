import hashlib
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.db.models import RawEmail, DedupFingerprint

logger = logging.getLogger(__name__)


def compute_checksum(sender: str, subject: str | None, body_text: str | None) -> str:
    raw = f"{sender}|{subject or ''}|{body_text or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def is_duplicate(db: AsyncSession, checksum: str) -> bool:
    result = await db.execute(
        select(DedupFingerprint).where(DedupFingerprint.fingerprint == checksum)
    )
    return result.scalar_one_or_none() is not None


async def store_raw_email(db: AsyncSession, payload: dict) -> RawEmail:
    from uuid import uuid4

    email = RawEmail(
        id=uuid4(),
        message_id=payload["message_id"],
        subject=payload.get("subject"),
        sender=payload["sender"],
        recipients=",".join(payload.get("recipients", [])),
        body_text=payload.get("body_text"),
        body_html=payload.get("body_html"),
        received_at=payload.get("received_at", datetime.utcnow()),
        source=payload.get("source", "smtp"),
        status="received",
        checksum=payload.get("checksum"),
        headers=payload.get("headers"),
    )
    db.add(email)
    await db.flush()
    return email


async def record_fingerprint(db: AsyncSession, email_id, message_id: str, checksum: str) -> DedupFingerprint:
    from uuid import uuid4

    fp = DedupFingerprint(
        id=uuid4(),
        fingerprint=checksum,
        message_id=message_id,
        email_id=email_id,
        created_at=datetime.utcnow(),
    )
    db.add(fp)
    await db.flush()
    return fp
