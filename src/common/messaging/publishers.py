import logging
from typing import Any

from src.common.messaging.celery_app import celery_app

logger = logging.getLogger(__name__)


def publish_event(routing_key: str, payload: dict[str, Any]) -> None:
    try:
        celery_app.send_task(routing_key, args=[payload])
        logger.debug("published event", routing_key=routing_key, event_id=payload.get("event_id"))
    except Exception as e:
        logger.error("failed to publish event", routing_key=routing_key, error=str(e))
        raise


def publish_raw_email_received(payload: dict[str, Any]) -> None:
    publish_event("raw.email.received", payload)


def publish_email_parsed(payload: dict[str, Any]) -> None:
    publish_event("email.parsed", payload)


def publish_email_classified(payload: dict[str, Any]) -> None:
    publish_event("email.classified", payload)


def publish_record_extracted(payload: dict[str, Any]) -> None:
    publish_event("record.extracted", payload)


def publish_record_persisted(payload: dict[str, Any]) -> None:
    publish_event("record.persisted", payload)


def publish_match_found(payload: dict[str, Any]) -> None:
    publish_event("match.found", payload)
