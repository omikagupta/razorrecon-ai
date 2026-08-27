from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI Finance Controller for Merchant Payment Reconciliation",
)


@app.get("/api/v1/health")
def health_check():
    database_status = "healthy"

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        database_status = "unhealthy"

    return {
        "status": "healthy" if database_status == "healthy" else "degraded",
        "service": settings.app_name,
        "database": database_status,
    }