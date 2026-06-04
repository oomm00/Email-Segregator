import hashlib
import logging
from datetime import datetime
from uuid import uuid4

from celery import shared_task
from sqlalchemy import select

from src.common.db.sync_session import SyncSession
from src.common.db.models import RawEmail, DedupFingerprint
from src.common.models.contracts import RawEmailReceived, EmailParsed
from src.common.messaging.publishers import publish_email_parsed

logger = logging.getLogger(__name__)


def _compute_checksum(sender: str, subject: str | None, body: str | None) -> str:
    raw = f"{sender}|{subject or ''}|{body or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()


@shared_task(name="raw.email.received", bind=True, max_retries=3, default_retry_delay=60, acks_late=True)
def handle_raw_email_received(self, payload: dict) -> dict:
    event = RawEmailReceived(**payload)
    logger.info("processing inbound email", email_id=str(event.email_id), message_id=event.message_id)

    session = SyncSession()
    try:
        checksum = _compute_checksum(event.sender, event.subject, event.body_text)

        existing = session.execute(
            select(DedupFingerprint).where(DedupFingerprint.fingerprint == checksum)
        ).scalar_one_or_none()
        if existing:
            logger.info("duplicate email, skipping", email_id=str(event.email_id))
            return {"email_id": str(event.email_id), "status": "duplicate"}

        email = RawEmail(
            id=event.email_id,
            message_id=event.message_id,
            subject=event.subject,
            sender=event.sender,
            recipients=",".join(event.recipients) if event.recipients else None,
            body_text=event.body_text,
            body_html=event.body_html,
            received_at=event.received_at,
            source=event.source,
            status="received",
            checksum=checksum,
            headers=event.headers,
        )
        session.add(email)
        session.flush()

        fp = DedupFingerprint(
            id=uuid4(),
            fingerprint=checksum,
            message_id=event.message_id,
            email_id=event.email_id,
        )
        session.add(fp)
        session.flush()

        parsed_event = EmailParsed(
            email_id=event.email_id,
            message_id=event.message_id,
            subject=event.subject,
            sender=event.sender,
            recipients=event.recipients or [],
            has_attachments=False,
            attachment_count=0,
            body_preview=(event.body_text or "")[:500],
        )
        publish_email_parsed(parsed_event.model_dump(mode="json"))

        email.status = "parsed"
        session.commit()

        logger.info("email ingested and parsed", email_id=str(event.email_id))
        return {"email_id": str(event.email_id), "status": "parsed"}

    except Exception as exc:
        session.rollback()
        logger.error("ingestion failed", email_id=str(event.email_id), error=str(exc))
        raise self.retry(exc=exc)
    finally:
        session.close()
