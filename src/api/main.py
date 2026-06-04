from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from src.common.config import settings
from src.common.exceptions import AppError, NotFoundError
from src.common.observability.logging import setup_logging, get_logger
from src.common.observability.tracing import CorrelationMiddleware, get_correlation_id
from src.common.db.session import engine
from src.common.storage.minio_client import storage
from src.common.search.es_client import es_client
from src.api.routers import health, inbound, admin
from src.common.auth.router import router as auth_router
from src.api.schemas.common import ErrorResponse

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info("starting service", service=settings.service_name, env=settings.app_env)
    try:
        await storage.ensure_bucket()
    except Exception as e:
        logger.warning("minio not available at startup", error=str(e))
    try:
        es = await es_client.ensure_connected()
        await es.info()
        logger.info("elasticsearch connected")
    except Exception as e:
        logger.warning("elasticsearch not available at startup", error=str(e))
    yield
    await es_client.close()
    await engine.dispose()
    logger.info("service stopped")


app = FastAPI(
    title="Shipping Email System",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationMiddleware)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    status_code = 404 if isinstance(exc, NotFoundError) else 400
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(detail=str(exc), correlation_id=get_correlation_id()).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled exception", error=str(exc))
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(detail="internal server error", correlation_id=get_correlation_id()).model_dump(),
    )


app.include_router(health.router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(inbound.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1/admin")
