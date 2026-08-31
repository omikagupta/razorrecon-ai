from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.models.reconciliation import (
    AuditLog,
    Evidence,
    ExceptionRecord,
    HumanReview,
)
from app.services.reconciliation.exception_service import ExceptionService


def create_exception(db, status="OPEN", exception_id="EXC_TEST_001"):
    exception = ExceptionRecord(
        exception_id=exception_id,
        transaction_id="pay_001",
        exception_type="AMOUNT_MISMATCH",
        severity="HIGH",
        status=status,
        confidence=Decimal("1.0000"),
        description="Test exception",
    )

    db.add(exception)
    db.commit()

    return exception


def test_get_exception_returns_exception_and_evidence(db):
    exception = create_exception(db)

    db.add(
        Evidence(
            exception_id=exception.exception_id,
            evidence_type="PAYMENT",
            source_table="payments",
            source_record_id="pay_001",
            description="Payment evidence",
        )
    )
    db.commit()

    service = ExceptionService(db)

    result = service.get_exception(
        exception.exception_id
    )

    assert result is not None

    returned_exception, evidence = result

    assert returned_exception.exception_id == exception.exception_id
    assert len(evidence) == 1
    assert evidence[0].evidence_type == "PAYMENT"


def test_get_exception_missing_returns_none(db):
    service = ExceptionService(db)

    result = service.get_exception(
        "EXC_DOES_NOT_EXIST"
    )

    assert result is None


def test_get_exception_by_id_returns_exception(db):
    exception = create_exception(db)

    service = ExceptionService(db)

    result = service.get_exception_by_id(
        exception.exception_id
    )

    assert result is not None
    assert result.exception_id == exception.exception_id


def test_get_exception_by_id_missing_returns_none(db):
    service = ExceptionService(db)

    result = service.get_exception_by_id(
        "EXC_DOES_NOT_EXIST"
    )

    assert result is None


def test_review_reject_escalates_exception(db):
    exception = create_exception(db)

    service = ExceptionService(db)

    result = service.review_exception(
        exception=exception,
        reviewer="reviewer@example.com",
        action="REJECT",
        reason="Settlement data is inconsistent.",
    )

    assert result["previous_state"] == "OPEN"
    assert result["new_state"] == "ESCALATED"
    assert exception.status == "ESCALATED"
    assert exception.resolved_at is None

    review = (
        db.query(HumanReview)
        .filter(
            HumanReview.exception_id
            == exception.exception_id
        )
        .first()
    )

    assert review is not None
    assert review.action == "REJECT"
    assert review.reviewer == "reviewer@example.com"

    audit = (
        db.query(AuditLog)
        .filter(
            AuditLog.transaction_id
            == exception.transaction_id
        )
        .first()
    )

    assert audit is not None
    assert audit.action == "EXCEPTION_REJECTED"
    assert audit.previous_state == "OPEN"
    assert audit.new_state == "ESCALATED"


def test_review_escalate_escalates_exception(db):
    exception = create_exception(
        db,
        exception_id="EXC_TEST_002",
    )

    service = ExceptionService(db)

    result = service.review_exception(
        exception=exception,
        reviewer="ops@example.com",
        action="ESCALATE",
        reason="Requires manual investigation.",
    )

    assert result["previous_state"] == "OPEN"
    assert result["new_state"] == "ESCALATED"
    assert exception.status == "ESCALATED"
    assert exception.resolved_at is None

    review = (
        db.query(HumanReview)
        .filter(
            HumanReview.exception_id
            == exception.exception_id
        )
        .first()
    )

    assert review.action == "ESCALATE"

    audit = (
        db.query(AuditLog)
        .filter(
            AuditLog.transaction_id
            == exception.transaction_id
        )
        .first()
    )

    assert audit.action == "EXCEPTION_ESCALATED"


def test_review_non_open_exception_is_rejected(db):
    exception = create_exception(
        db,
        status="RESOLVED",
        exception_id="EXC_TEST_003",
    )

    service = ExceptionService(db)

    with pytest.raises(
        ValueError,
        match="Only OPEN exceptions can be reviewed.",
    ):
        service.review_exception(
            exception=exception,
            reviewer="reviewer@example.com",
            action="APPROVE",
            reason="Already resolved.",
        )


def test_review_invalid_action_is_rejected(db):
    exception = create_exception(
        db,
        exception_id="EXC_TEST_004",
    )

    service = ExceptionService(db)

    with pytest.raises(
        ValueError,
        match="Invalid review action.",
    ):
        service.review_exception(
            exception=exception,
            reviewer="reviewer@example.com",
            action="INVALID",
            reason="Invalid action.",
        )


def test_review_rolls_back_when_commit_fails(db):
    exception = create_exception(
        db,
        exception_id="EXC_TEST_005",
    )

    service = ExceptionService(db)

    original_commit = db.commit

    def failing_commit():
        raise RuntimeError("Database commit failed")

    db.commit = failing_commit

    with pytest.raises(
        RuntimeError,
        match="Database commit failed",
    ):
        service.review_exception(
            exception=exception,
            reviewer="reviewer@example.com",
            action="APPROVE",
            reason="Approve exception.",
        )

    db.commit = original_commit

    db.rollback()

    refreshed = (
        db.query(ExceptionRecord)
        .filter(
            ExceptionRecord.exception_id
            == exception.exception_id
        )
        .first()
    )

    assert refreshed.status == "OPEN"
    assert refreshed.resolved_at is None

    reviews = (
        db.query(HumanReview)
        .filter(
            HumanReview.exception_id
            == exception.exception_id
        )
        .all()
    )

    assert reviews == []