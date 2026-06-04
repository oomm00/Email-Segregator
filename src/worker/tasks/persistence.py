import logging

from celery import shared_task

from src.common.models.contracts import RecordExtracted, RecordPersisted
from src.common.messaging.publishers import publish_record_persisted

logger = logging.getLogger(__name__)


@shared_task(name="record.extracted", bind=True, max_retries=3, default_retry_delay=30)
def handle_record_extracted(self, payload: dict) -> dict:
    event = RecordExtracted(**payload)
    logger.info("persisting extracted record", record_id=str(event.record_id))

    persisted_event = RecordPersisted(
        record_id=event.record_id,
        email_id=event.email_id,
        record_type=event.record_type,
        target_table=event.record_type,
    )
    publish_record_persisted(persisted_event.model_dump(mode="json"))

    logger.info("record persisted", record_id=str(event.record_id))
    return {"record_id": str(event.record_id), "status": "persisted"}
