from src.common.messaging.celery_app import celery_app

celery_app.conf.update(
    imports=[
        "src.worker.tasks.ingestion",
        "src.worker.tasks.classification",
        "src.worker.tasks.extraction",
        "src.worker.tasks.matching",
        "src.worker.tasks.persistence",
        "src.worker.tasks.search_index",
    ],
)

__all__ = ["celery_app"]
