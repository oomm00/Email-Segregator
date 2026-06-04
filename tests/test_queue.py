from src.common.messaging.celery_app import celery_app


def test_celery_app_created():
    assert celery_app.main == "shipping_email"
    assert celery_app.conf.task_serializer == "json"


def test_celery_routes_defined():
    routes = celery_app.conf.task_routes
    assert "raw.email.received" in routes
    assert "email.parsed" in routes
    assert "email.classified" in routes
    assert "record.extracted" in routes
    assert "record.persisted" in routes
    assert "match.found" in routes


def test_celery_broker_url():
    assert celery_app.conf.broker_url is not None
    assert len(celery_app.conf.broker_url) > 0


def test_celery_result_backend():
    assert celery_app.conf.result_backend is not None
    assert len(celery_app.conf.result_backend) > 0
