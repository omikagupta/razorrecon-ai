
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
    ) -> tuple[list[ExceptionRecord], int]:
        """
        Return filtered and paginated exceptions.

        Returns:
            (
                exceptions,
                total
            )

        Where:
            exceptions = current page of ExceptionRecord objects
            total = total number of records matching the filters
        """

        query = self.db.query(ExceptionRecord)

        # ---------------------------------------------------------
        # FILTER BY STATUS
        # ---------------------------------------------------------

        if status:
            query = query.filter(
                ExceptionRecord.status == status
            )

        # ---------------------------------------------------------
        # FILTER BY SEVERITY
        # ---------------------------------------------------------

        if severity:
            query = query.filter(
                ExceptionRecord.severity == severity
            )

        # ---------------------------------------------------------
        # FILTER BY EXCEPTION TYPE
        # ---------------------------------------------------------

        if exception_type:
            query = query.filter(
                ExceptionRecord.exception_type == exception_type
            )

        # ---------------------------------------------------------
        # COUNT TOTAL MATCHING RECORDS
        # ---------------------------------------------------------

        total = query.count()

        # ---------------------------------------------------------
        # APPLY ORDERING + PAGINATION
        # ---------------------------------------------------------

        exceptions = (
            query
            .order_by(
                ExceptionRecord.created_at.desc(),
                ExceptionRecord.id.desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

        # ---------------------------------------------------------
        # RETURN BOTH PAGE + TOTAL
        # ---------------------------------------------------------

        return exceptions, total

    def get_evidence(
        self,
        exception_id: str,
    ) -> list[Evidence]:
        """
        Return evidence associated with an exception.

        Evidence is returned in ascending database ID order.
        """

        return (
            self.db.query(Evidence)
            .filter(
                Evidence.exception_id == exception_id
            )
            .order_by(Evidence.id)
            .all()
        )
