from sqlalchemy.orm import Session

from app.repositories.exception_repository import (
    ExceptionRepository,
)


class ExceptionService:

    def __init__(self, db: Session):
        self.repository = ExceptionRepository(db)

    def list_exceptions(
        self,
        status: str | None = None,
        severity: str | None = None,
        exception_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ):
        return self.repository.list(
            status=status,
            severity=severity,
            exception_type=exception_type,
            limit=limit,
            offset=offset,
        )

    def get_exception(
        self,
        exception_id: str,
    ):
        exception = self.repository.get_by_id(exception_id)

        if exception is None:
            return None

        evidence = self.repository.get_evidence(
            exception_id
        )

        return exception, evidence