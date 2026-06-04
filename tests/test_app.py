import pytest
from src.api.main import app


def test_app_created():
    assert app.title == "Shipping Email System"
    assert app.version == "0.1.0"


def test_app_routes_registered():
    routes = [r.path for r in app.routes]
    assert "/health" in routes
    assert "/ready" in routes
    assert "/version" in routes
    assert "/api/v1/inbound/email" in routes
    assert "/api/v1/admin/email/upload" in routes
    assert "/metrics" in routes
