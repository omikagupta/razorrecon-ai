from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.reconciliation import (
    Evidence,
    ExceptionRecord,
)


class ExceptionRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        exception_id: str,
    ) -> ExceptionRecord | None:
        return (
            self.db.query(ExceptionRecord)
            .filter(
                ExceptionRecord.exception_id == exception_id
            )
            .first()
        )

    def list(
        self,
        status: str | None = None,
        severity: str | None = None,
        exception_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ExceptionRecord]:

        query = self.db.query(ExceptionRecord)

        if status:
            query = query.filter(
                ExceptionRecord.status == status
            )

        if severity:
            query = query.filter(
                ExceptionRecord.severity == severity
            )

        if exception_type:
            query = query.filter(
                ExceptionRecord.exception_type == exception_type
            )

        return (
            query
            .order_by(ExceptionRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_evidence(
        self,
        exception_id: str,
    ) -> list[Evidence]:

        return (
            self.db.query(Evidence)
            .filter(
                Evidence.exception_id == exception_id
            )
            .order_by(Evidence.id)
            .all()
        )
