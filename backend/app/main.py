
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.exceptions import router as exceptions_router
from app.api.v1.reconciliation_runs import (
    router as reconciliation_runs_router,
)
from app.core.config import settings
from app.core.error_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging
from app.core.request_logging import RequestLoggingMiddleware
from app.db.session import engine


# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown lifecycle events.
    """
    logger.info(
        "application_started app=%s environment=%s",
        settings.app_name,
        settings.app_env,
    )

    yield

    logger.info(
        "application_stopped app=%s",
        settings.app_name,
    )


# ------------------------------------------------------------------
# Application
# ------------------------------------------------------------------

app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version="0.2.0",
    contact={"name": "RazorRecon AI"},
    license_info={"name": "Proprietary"},
    openapi_tags=[
        {
            "name": "System",
            "description": "Service metadata and API information.",
        },
        {
            "name": "Health",
            "description": (
                "Liveness and readiness checks for service monitoring."
            ),
        },
        {
            "name": "Exceptions",
            "description": (
                "Reconciliation exception lookup, analytics, "
                "investigation, and human-review workflows."
            ),
        },
        {
            "name": "Dashboard",
            "description": (
                "Aggregate reconciliation and exception metrics."
            ),
        },
    ],
    description=(
        "RazorRecon AI — Intelligent financial reconciliation "
        "and exception management platform."
    ),
)

app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    Exception,
    unhandled_exception_handler,
)


# ------------------------------------------------------------------
# Request Logging
# ------------------------------------------------------------------

app.add_middleware(RequestLoggingMiddleware)


# ------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Content-Type",
        "Authorization",
    ],
)


# ------------------------------------------------------------------
# API Routers
# ------------------------------------------------------------------

app.include_router(exceptions_router)
app.include_router(dashboard_router)
app.include_router(reconciliation_runs_router)


# ------------------------------------------------------------------
# Health Endpoints
# ------------------------------------------------------------------


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    """
    Returns the overall application health status.

    Verifies database connectivity and reports whether the
    service is healthy or degraded.
    """
    database_status = "healthy"

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        logger.exception("database_health_check_failed")
        database_status = "unhealthy"

    return {
        "status": (
            "healthy"
            if database_status == "healthy"
            else "degraded"
        ),
        "service": settings.app_name,
        "database": database_status,
    }


@app.get("/api/v1/health/live", tags=["Health"])
def liveness_check():
    """
    Confirms that the application process is alive.

    This endpoint intentionally does not check external
    dependencies such as the database.
    """
    return {
        "status": "alive",
        "service": settings.app_name,
    }


@app.get("/api/v1/health/ready", tags=["Health"])
def readiness_check():
    """
    Confirms that the application is ready to serve traffic.

    Readiness requires successful database connectivity.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "database": "healthy",
        }

    except Exception:
        logger.exception("database_readiness_check_failed")

        return {
            "status": "not_ready",
            "database": "unhealthy",
        }


# ------------------------------------------------------------------
# System Endpoints
# ------------------------------------------------------------------


@app.get("/api/v1", tags=["System"])
def api_root():
    """
    Basic API information endpoint.
    """
    return {
        "service": settings.app_name,
        "version": "0.2.0",
        "status": "running",
        "message": "RazorRecon AI API is operational.",
    }

