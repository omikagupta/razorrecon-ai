from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.reconciliation import (
    AuditLog,
    HumanReview,
)

from app.repositories.exception_repository import (
    ExceptionRepository,
)


class ExceptionService:

    def __init__(self, db: Session):
        self.db = db
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
        exception = self.repository.get_by_id(
            exception_id
        )

        if exception is None:
            return None

        evidence = self.repository.get_evidence(
            exception_id
        )

        return exception, evidence

    def get_exception_by_id(
        self,
        exception_id: str,
    ):
        return self.repository.get_by_id(
            exception_id
        )

    def review_exception(
        self,
        exception,
        reviewer: str,
        action: str,
        reason: str,
    ) -> dict:
        """
        Apply a human review decision atomically.

        Persists:
        - exception lifecycle state
        - human review record
        - audit log

        All three changes belong to the same
        database transaction.
        """

        if exception.status != "OPEN":
            raise ValueError(
                "Only OPEN exceptions can be reviewed."
            )

        action_mapping = {
            "APPROVE": {
                "new_state": "RESOLVED",
                "audit_action": "EXCEPTION_RESOLVED",
            },
            "REJECT": {
                "new_state": "ESCALATED",
                "audit_action": "EXCEPTION_REJECTED",
            },
            "ESCALATE": {
                "new_state": "ESCALATED",
                "audit_action": "EXCEPTION_ESCALATED",
            },
        }

        if action not in action_mapping:
            raise ValueError(
                "Invalid review action."
            )

        transition = action_mapping[action]

        previous_state = exception.status
        new_state = transition["new_state"]
        audit_action = transition["audit_action"]

        now = datetime.now(UTC)

        try:
            exception.status = new_state

            if new_state == "RESOLVED":
                exception.resolved_at = now

            human_review = HumanReview(
                exception_id=exception.exception_id,
                reviewer=reviewer,
                action=action,
                reason=reason,
                created_at=now,
            )

            self.db.add(human_review)

            audit_log = AuditLog(
                transaction_id=exception.transaction_id,
                actor=reviewer,
                action=audit_action,
                previous_state=previous_state,
                new_state=new_state,
                reason=reason,
                confidence=exception.confidence,
                created_at=now,
            )

            self.db.add(audit_log)

            self.db.commit()
            self.db.refresh(exception)

        except Exception:
            self.db.rollback()
            raise

        return {
            "exception": exception,
            "previous_state": previous_state,
            "new_state": new_state,
        }