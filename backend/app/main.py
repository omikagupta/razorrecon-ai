from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.exceptions import router as exceptions_router
from app.core.config import settings
from app.db.session import engine


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    contact={"name": "RazorRecon AI"},
    license_info={"name": "Proprietary"},
    openapi_tags=[
        {
            "name": "System",
            "description": "Service availability and API metadata.",
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
            "description": "Aggregate reconciliation and exception metrics.",
        },
    ],
    description=(
        "RazorRecon AI — Intelligent financial reconciliation "
        "and exception management platform."
    ),
)


# ------------------------------------------------------------------
# API Routers
# ------------------------------------------------------------------

app.include_router(exceptions_router)
app.include_router(dashboard_router)


# ------------------------------------------------------------------
# System Endpoints
# ------------------------------------------------------------------

@app.get("/api/v1/health", tags=["System"])
def health_check():
    """
    Health check endpoint.

    Verifies that the API is running and the PostgreSQL
    database is reachable.
    """
    database_status = "healthy"

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
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
