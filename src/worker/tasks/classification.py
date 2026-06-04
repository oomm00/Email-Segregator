import logging

from celery import shared_task

from src.common.models.contracts import EmailParsed, EmailClassified
from src.common.messaging.publishers import publish_email_classified

logger = logging.getLogger(__name__)


@shared_task(name="email.parsed", bind=True, max_retries=3, default_retry_delay=30)
def handle_email_parsed(self, payload: dict) -> dict:
    event = EmailParsed(**payload)
    logger.info("classifying email", email_id=str(event.email_id), subject=event.subject)

    classified_event = EmailClassified(
        email_id=event.email_id,
        message_id=event.message_id,
        category="general",
        confidence=1.0,
        labels=["parsed"],
    )
    publish_email_classified(classified_event.model_dump(mode="json"))

    return {"email_id": str(event.email_id), "status": "classified"}
