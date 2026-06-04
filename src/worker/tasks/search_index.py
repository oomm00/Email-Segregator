import asyncio
import logging

from celery import shared_task

from src.common.models.contracts import RecordPersisted
from src.common.search.es_client import es_client, INDEX_EMAILS

logger = logging.getLogger(__name__)


@shared_task(name="record.persisted", bind=True, max_retries=3, default_retry_delay=30)
def handle_record_persisted(self, payload: dict) -> dict:
    event = RecordPersisted(**payload)
    logger.info("indexing record in elasticsearch", record_id=str(event.record_id))

    async def _index():
        body = {
            "email_id": str(event.email_id),
            "record_id": str(event.record_id),
            "record_type": event.record_type,
            "target_table": event.target_table,
            "persisted_at": event.persisted_at.isoformat(),
        }
        try:
            await es_client.ensure_index(INDEX_EMAILS)
            await es_client.index_doc(INDEX_EMAILS, str(event.record_id), body)
            logger.info("indexed in es", record_id=str(event.record_id))
        except Exception as e:
            logger.error("es indexing failed", record_id=str(event.record_id), error=str(e))
            raise

    try:
        asyncio.run(_index())
    except Exception as exc:
        logger.error("search indexing failed", record_id=str(event.record_id), error=str(exc))
        raise self.retry(exc=exc)

    return {"record_id": str(event.record_id), "status": "indexed"}
