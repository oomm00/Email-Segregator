import asyncio

from fastapi import APIRouter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from redis import asyncio as aioredis
from sqlalchemy import text
from starlette.responses import Response

from src.common.config import settings
from src.common.db.session import async_session
from src.common.messaging.celery_app import celery_app
from src.common.storage.minio_client import storage
from src.common.search.es_client import es_client
from src.api.schemas.common import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version="0.1.0",
    )


@router.get("/ready")
async def readiness() -> HealthResponse:
    checks = await asyncio.gather(
        _check_db(),
        _check_redis(),
        _check_rabbitmq(),
        _check_elasticsearch(),
        _check_minio(),
        return_exceptions=True,
    )
    statuses = {
        "database": checks[0],
        "redis": checks[1],
        "rabbitmq": checks[2],
        "elasticsearch": checks[3],
        "minio": checks[4],
    }

    all_ok = all(s is True for s in statuses.values())
    detail = {svc: "ok" if s is True else str(s) for svc, s in statuses.items()}
    overall = "ok" if all_ok else "degraded"
    status_code = 200 if all_ok else 503

    return HealthResponse(
        status=overall,
        service=settings.service_name,
        version="0.1.0",
        checks=detail,
    )


@router.get("/version")
async def version() -> dict:
    return {"service": settings.service_name, "version": "0.1.0", "env": settings.app_env}


@router.get("/metrics")
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def _check_db() -> bool:
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        return e


async def _check_redis() -> bool:
    try:
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        return True
    except Exception as e:
        return e


async def _check_rabbitmq() -> bool:
    try:
        with celery_app.connection_for_read() as conn:
            conn.ensure_connection(max_retries=1)
            return True
    except Exception as e:
        return e


async def _check_elasticsearch() -> bool:
    try:
        es = await es_client.ensure_connected()
        await es.info()
        return True
    except Exception as e:
        return e


async def _check_minio() -> bool:
    try:
        return await storage.health()
    except Exception as e:
        return e
