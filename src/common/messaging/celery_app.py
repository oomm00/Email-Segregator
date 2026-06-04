from celery import Celery

from src.common.config import settings

celery_app = Celery(
    "shipping_email",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_soft_time_limit=300,
    task_time_limit=600,
    task_routes={
        "raw.email.received": {"queue": "ingestion"},
        "email.parsed": {"queue": "classification"},
        "email.classified": {"queue": "extraction"},
        "record.extracted": {"queue": "persistence"},
        "record.persisted": {"queue": "search"},
        "match.found": {"queue": "matching"},
    },
    task_queues={
        "ingestion": {"exchange": "shipping.email", "routing_key": "raw.email.received"},
        "classification": {"exchange": "shipping.email", "routing_key": "email.parsed"},
        "extraction": {"exchange": "shipping.email", "routing_key": "email.classified"},
        "persistence": {"exchange": "shipping.email", "routing_key": "record.extracted"},
        "search": {"exchange": "shipping.email", "routing_key": "record.persisted"},
        "matching": {"exchange": "shipping.email", "routing_key": "match.found"},
    },
    task_default_queue="default",
    task_default_exchange="shipping.email",
    task_default_exchange_type="topic",
)
