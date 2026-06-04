import logging
from uuid import uuid4

from celery import shared_task
from sqlalchemy import select

from src.common.db.sync_session import SyncSession
from src.common.db.models import RawEmail
from src.common.models.contracts import EmailClassified, RecordExtracted
from src.common.messaging.publishers import publish_record_extracted
from src.extraction.pipeline import run_tonnage_pipeline
from src.extraction_cargo.pipeline import run_cargo_vc_pipeline
from src.extraction_tc.pipeline import run_tc_pipeline

logger = logging.getLogger(__name__)


@shared_task(name="email.classified", bind=True, max_retries=3, default_retry_delay=30)
def handle_email_classified(self, payload: dict) -> dict:
    event = EmailClassified(**payload)
    logger.info("extracting from classified email", email_id=str(event.email_id), category=event.category)

    if event.category.upper() == "TONNAGE":
        return _extract_tonnage(event)
    if event.category.upper() == "CARGO_VC":
        return _extract_cargo_vc(event)
    if event.category.upper() == "CARGO_TC":
        return _extract_cargo_tc(event)
    return {"email_id": str(event.email_id), "status": "skipped", "reason": f"unknown_category:{event.category}"}


def _extract_tonnage(event: EmailClassified) -> dict:
    session = SyncSession()
    try:
        result = session.execute(select(RawEmail).where(RawEmail.id == event.email_id))
        email = result.scalar_one_or_none()
        if not email:
            logger.error("raw email not found", email_id=str(event.email_id))
            return {"email_id": str(event.email_id), "status": "error", "reason": "email_not_found"}

        body = email.body_text or ""
        subject = email.subject or ""
        vessels = run_tonnage_pipeline(str(event.email_id), body, subject)

        if not vessels:
            logger.warning("no vessels extracted", email_id=str(event.email_id))
            return {"email_id": str(event.email_id), "status": "no_vessels"}

        for v in vessels:
            record = RecordExtracted(
                record_id=uuid4(),
                email_id=event.email_id,
                record_type="TONNAGE_VESSEL",
                data=v.to_record_dict(),
                confidence=v.overall_confidence,
            )
            publish_record_extracted(record.model_dump(mode="json"))

        logger.info("tonnage extraction complete", email_id=str(event.email_id), vessel_count=len(vessels))
        return {"email_id": str(event.email_id), "status": "extracted", "vessels": len(vessels)}

    except Exception as exc:
        logger.error("tonnage extraction failed", email_id=str(event.email_id), error=str(exc))
        raise self.retry(exc=exc)
    finally:
        session.close()


def _extract_cargo_vc(event: EmailClassified) -> dict:
    session = SyncSession()
    try:
        result = session.execute(select(RawEmail).where(RawEmail.id == event.email_id))
        email = result.scalar_one_or_none()
        if not email:
            logger.error("raw email not found", email_id=str(event.email_id))
            return {"email_id": str(event.email_id), "status": "error", "reason": "email_not_found"}

        body = email.body_text or ""
        subject = email.subject or ""
        cargoes = run_cargo_vc_pipeline(str(event.email_id), body, subject)

        if not cargoes:
            logger.warning("no cargoes extracted", email_id=str(event.email_id))
            return {"email_id": str(event.email_id), "status": "no_cargoes"}

        for c in cargoes:
            record = RecordExtracted(
                record_id=uuid4(),
                email_id=event.email_id,
                record_type="CARGO_VC",
                data=c.to_record_dict(),
                confidence=c.overall_confidence,
            )
            publish_record_extracted(record.model_dump(mode="json"))

        logger.info("cargo vc extraction complete", email_id=str(event.email_id), cargo_count=len(cargoes))
        return {"email_id": str(event.email_id), "status": "extracted", "cargoes": len(cargoes)}

    except Exception as exc:
        logger.error("cargo vc extraction failed", email_id=str(event.email_id), error=str(exc))
        raise self.retry(exc=exc)
    finally:
        session.close()


def _extract_cargo_tc(event: EmailClassified) -> dict:
    session = SyncSession()
    try:
        result = session.execute(select(RawEmail).where(RawEmail.id == event.email_id))
        email = result.scalar_one_or_none()
        if not email:
            logger.error("raw email not found", email_id=str(event.email_id))
            return {"email_id": str(event.email_id), "status": "error", "reason": "email_not_found"}

        body = email.body_text or ""
        subject = email.subject or ""
        fixtures = run_tc_pipeline(str(event.email_id), body, subject)

        if not fixtures:
            logger.warning("no tc fixtures extracted", email_id=str(event.email_id))
            return {"email_id": str(event.email_id), "status": "no_tc_fixtures"}

        for tf in fixtures:
            record = RecordExtracted(
                record_id=uuid4(),
                email_id=event.email_id,
                record_type="CARGO_TC",
                data=tf.to_record_dict(),
                confidence=tf.overall_confidence,
            )
            publish_record_extracted(record.model_dump(mode="json"))

        logger.info("tc extraction complete", email_id=str(event.email_id), tc_count=len(fixtures))
        return {"email_id": str(event.email_id), "status": "extracted", "tc_fixtures": len(fixtures)}

    except Exception as exc:
        logger.error("tc extraction failed", email_id=str(event.email_id), error=str(exc))
        raise self.retry(exc=exc)
    finally:
        session.close()
