from datetime import datetime, timedelta
from decimal import Decimal

from app.models.reconciliation import (
    Evidence,
    ExceptionRecord,
)
from app.repositories.exception_repository import (
    ExceptionRepository,
)


def create_exception(
    db,
    exception_id,
    exception_type="AMOUNT_MISMATCH",
    severity="HIGH",
    status="OPEN",
    created_at=None,
):
    exception = ExceptionRecord(
        exception_id=exception_id,
        transaction_id=f"pay_{exception_id}",
        exception_type=exception_type,
        severity=severity,
        status=status,
        confidence=Decimal("1.0000"),
        description="Test exception",
        created_at=created_at or datetime.now(),
    )

    db.add(exception)
    db.commit()

    return exception


def test_get_by_id_returns_exception(db):
    create_exception(
        db,
        exception_id="EXC_001",
    )

    repository = ExceptionRepository(db)

    result = repository.get_by_id("EXC_001")

    assert result is not None
    assert result.exception_id == "EXC_001"


def test_get_by_id_returns_none_for_missing_exception(db):
    repository = ExceptionRepository(db)

    result = repository.get_by_id("EXC_DOES_NOT_EXIST")

    assert result is None


def test_list_returns_exceptions_newest_first(db):
    now = datetime.now()

    create_exception(
        db,
        exception_id="EXC_001",
        created_at=now - timedelta(minutes=2),
    )

    create_exception(
        db,
        exception_id="EXC_002",
        created_at=now,
    )

    repository = ExceptionRepository(db)

    results = repository.list()

    assert len(results) == 2
    assert results[0].exception_id == "EXC_002"
    assert results[1].exception_id == "EXC_001"


def test_list_filters_by_status(db):
    create_exception(
        db,
        exception_id="EXC_OPEN",
        status="OPEN",
    )

    create_exception(
        db,
        exception_id="EXC_RESOLVED",
        status="RESOLVED",
    )

    repository = ExceptionRepository(db)

    results = repository.list(
        status="OPEN",
    )

    assert len(results) == 1
    assert results[0].exception_id == "EXC_OPEN"


def test_list_filters_by_severity(db):
    create_exception(
        db,
        exception_id="EXC_HIGH",
        severity="HIGH",
    )

    create_exception(
        db,
        exception_id="EXC_CRITICAL",
        severity="CRITICAL",
    )

    repository = ExceptionRepository(db)

    results = repository.list(
        severity="CRITICAL",
    )

    assert len(results) == 1
    assert results[0].exception_id == "EXC_CRITICAL"


def test_list_filters_by_exception_type(db):
    create_exception(
        db,
        exception_id="EXC_AMOUNT",
        exception_type="AMOUNT_MISMATCH",
    )

    create_exception(
        db,
        exception_id="EXC_MISSING",
        exception_type="MISSING_SETTLEMENT",
    )

    repository = ExceptionRepository(db)

    results = repository.list(
        exception_type="MISSING_SETTLEMENT",
    )

    assert len(results) == 1
    assert results[0].exception_id == "EXC_MISSING"


def test_list_supports_combined_filters(db):
    create_exception(
        db,
        exception_id="EXC_MATCH",
        status="OPEN",
        severity="HIGH",
        exception_type="AMOUNT_MISMATCH",
    )

    create_exception(
        db,
        exception_id="EXC_WRONG_STATUS",
        status="RESOLVED",
        severity="HIGH",
        exception_type="AMOUNT_MISMATCH",
    )

    create_exception(
        db,
        exception_id="EXC_WRONG_SEVERITY",
        status="OPEN",
        severity="CRITICAL",
        exception_type="AMOUNT_MISMATCH",
    )

    repository = ExceptionRepository(db)

    results = repository.list(
        status="OPEN",
        severity="HIGH",
        exception_type="AMOUNT_MISMATCH",
    )

    assert len(results) == 1
    assert results[0].exception_id == "EXC_MATCH"


def test_list_supports_limit_and_offset(db):
    now = datetime.now()

    for index in range(3):
        create_exception(
            db,
            exception_id=f"EXC_{index}",
            created_at=now + timedelta(seconds=index),
        )

    repository = ExceptionRepository(db)

    results = repository.list(
        limit=1,
        offset=1,
    )

    assert len(results) == 1
    assert results[0].exception_id == "EXC_1"


def test_get_evidence_returns_evidence_in_id_order(db):
    create_exception(
        db,
        exception_id="EXC_EVIDENCE",
    )

    evidence_1 = Evidence(
        exception_id="EXC_EVIDENCE",
        evidence_type="PAYMENT",
        source_table="payments",
        source_record_id="pay_001",
        description="Payment evidence",
    )

    evidence_2 = Evidence(
        exception_id="EXC_EVIDENCE",
        evidence_type="SETTLEMENT",
        source_table="settlements",
        source_record_id="set_001",
        description="Settlement evidence",
    )

    db.add_all(
        [
            evidence_1,
            evidence_2,
        ]
    )
    db.commit()

    repository = ExceptionRepository(db)

    results = repository.get_evidence(
        "EXC_EVIDENCE",
    )

    assert len(results) == 2
    assert results[0].evidence_type == "PAYMENT"
    assert results[1].evidence_type == "SETTLEMENT"


def test_get_evidence_returns_empty_list_when_none_exist(db):
    repository = ExceptionRepository(db)

    results = repository.get_evidence(
        "EXC_NO_EVIDENCE",
    )

    assert results == []