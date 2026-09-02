
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

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
from app.core.request_logging import RequestLoggingMiddleware
from app.db.session import engine


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="RazorRecon AI",
    description=(
        "AI-powered financial reconciliation and "
        "exception investigation platform."
    ),
    version="0.2.0",
)


# =========================================================
# MIDDLEWARE
# =========================================================

# Allow the configured frontend origins to communicate
# with the FastAPI backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    RequestLoggingMiddleware,
)


# =========================================================
# ERROR HANDLERS
# =========================================================

app.add_exception_handler(
    HTTPException,
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


# =========================================================
# SYSTEM ROUTES
# =========================================================

@app.get(
    "/api/v1",
    tags=["System"],
)
def api_root():
    return {
        "service": "RazorRecon AI",
        "status": "running",
        "version": "0.2.0",
    }


# =========================================================
# API ROUTERS
#
# Prefixes are already defined inside each router file.
# Do NOT add prefix= here.
# =========================================================

app.include_router(dashboard_router)

app.include_router(exceptions_router)

app.include_router(reconciliation_runs_router)


# =========================================================
# HEALTH CHECKS
# =========================================================

@app.get(
    "/api/v1/health",
    tags=["Health"],
)
def health_check():
    """
    Liveness + database health check.

    Returns:
        healthy  -> database connection succeeds
        degraded -> database connection fails

    HTTP status remains 200 because this endpoint reports
    service health rather than rejecting the request.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "service": "RazorRecon AI",
            "database": "healthy",
        }

    except Exception:
        return {
            "status": "degraded",
            "service": "RazorRecon AI",
            "database": "unhealthy",
        }


@app.get(
    "/api/v1/health/live",
    tags=["Health"],
)
def liveness_check():
    """
    Kubernetes-style liveness check.

    This endpoint does not depend on the database.
    """
    return {
        "status": "alive",
        "service": "RazorRecon AI",
    }


@app.get(
    "/api/v1/health/ready",
    tags=["Health"],
)
def readiness_check():
    """
    Readiness check.

    The application is ready only when the database
    connection is available.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "service": "RazorRecon AI",
            "database": "healthy",
        }

    except Exception:
        return {
            "status": "not_ready",
            "service": "RazorRecon AI",
            "database": "unhealthy",
        }

