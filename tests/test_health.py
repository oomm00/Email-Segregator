import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "shipping-email"
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_ready_endpoint(client: AsyncClient):
    resp = await client.get("/ready")
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data
    assert data["service"] == "shipping-email"


@pytest.mark.asyncio
async def test_version_endpoint(client: AsyncClient):
    resp = await client.get("/version")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "0.1.0"
    assert data["env"] is not None


@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient):
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/plain; charset=utf-8; version=0.0.4"
    assert b"emails_received_total" in resp.content


@pytest.mark.asyncio
async def test_inbound_email_endpoint(client: AsyncClient):
    resp = await client.post(
        "/api/v1/inbound/email",
        json={
            "message_id": "<test@example.com>",
            "sender": "sender@example.com",
            "recipients": ["recipient@example.com"],
            "subject": "Test",
            "body_text": "Hello",
        },
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "accepted"
    assert "email_id" in data


@pytest.mark.asyncio
async def test_inbound_email_missing_required(client: AsyncClient):
    resp = await client.post("/api/v1/inbound/email", json={})
    assert resp.status_code == 422
