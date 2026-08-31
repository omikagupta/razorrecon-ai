from decimal import Decimal

from app.models.reconciliation import (
    ExceptionRecord,
    ReconciliationResult,
)
from app.services.reconciliation.analytics import (
    get_exception_analytics,
)


def test_empty_analytics(db):
    result = get_exception_analytics(db)

    assert result["total_exceptions"] == 0
    assert result["open_exceptions"] == 0
    assert result["resolved_exceptions"] == 0
    assert result["escalated_exceptions"] == 0
    assert result["resolution_rate"] == 0
    assert result["financial_exposure"] == "0.00"


def test_exception_status_counts(db):
    db.add_all(
        [
            ExceptionRecord(
                exception_id="EXC_001",
                transaction_id="pay_001",
                exception_type="AMOUNT_MISMATCH",
                severity="HIGH",
                status="OPEN",
                confidence=Decimal("1.0000"),
            ),
            ExceptionRecord(
                exception_id="EXC_002",
                transaction_id="pay_002",
                exception_type="MISSING_SETTLEMENT",
                severity="CRITICAL",
                status="RESOLVED",
                confidence=Decimal("1.0000"),
            ),
            ExceptionRecord(
                exception_id="EXC_003",
                transaction_id="pay_003",
                exception_type="AMOUNT_MISMATCH",
                severity="MEDIUM",
                status="ESCALATED",
                confidence=Decimal("0.9000"),
            ),
        ]
    )

    db.commit()

    result = get_exception_analytics(db)

    assert result["total_exceptions"] == 3
    assert result["open_exceptions"] == 1
    assert result["resolved_exceptions"] == 1
    assert result["escalated_exceptions"] == 1
    assert result["resolution_rate"] == round(1 / 3, 4)


def test_severity_distribution(db):
    db.add_all(
        [
            ExceptionRecord(
                exception_id="EXC_101",
                transaction_id="pay_101",
                exception_type="AMOUNT_MISMATCH",
                severity="HIGH",
                status="OPEN",
                confidence=Decimal("1.0000"),
            ),
            ExceptionRecord(
                exception_id="EXC_102",
                transaction_id="pay_102",
                exception_type="MISSING_SETTLEMENT",
                severity="CRITICAL",
                status="OPEN",
                confidence=Decimal("1.0000"),
            ),
            ExceptionRecord(
                exception_id="EXC_103",
                transaction_id="pay_103",
                exception_type="AMOUNT_MISMATCH",
                severity="HIGH",
                status="RESOLVED",
                confidence=Decimal("1.0000"),
            ),
        ]
    )

    db.commit()

    result = get_exception_analytics(db)

    assert result["severity_distribution"]["HIGH"] == 2
    assert result["severity_distribution"]["CRITICAL"] == 1
    assert result["severity_distribution"]["MEDIUM"] == 0
    assert result["severity_distribution"]["LOW"] == 0


def test_exception_type_distribution(db):
    db.add_all(
        [
            ExceptionRecord(
                exception_id="EXC_201",
                transaction_id="pay_201",
                exception_type="AMOUNT_MISMATCH",
                severity="HIGH",
                status="OPEN",
                confidence=Decimal("1.0000"),
            ),
            ExceptionRecord(
                exception_id="EXC_202",
                transaction_id="pay_202",
                exception_type="AMOUNT_MISMATCH",
                severity="HIGH",
                status="OPEN",
                confidence=Decimal("1.0000"),
            ),
            ExceptionRecord(
                exception_id="EXC_203",
                transaction_id="pay_203",
                exception_type="MISSING_SETTLEMENT",
                severity="CRITICAL",
                status="OPEN",
                confidence=Decimal("1.0000"),
            ),
        ]
    )

    db.commit()

    result = get_exception_analytics(db)

    assert result["exception_type_distribution"] == {
        "AMOUNT_MISMATCH": 2,
        "MISSING_SETTLEMENT": 1,
    }


def test_financial_exposure(db):
    db.add_all(
        [
            ReconciliationResult(
                run_id="RUN_001",
                transaction_id="pay_301",
                status="AMOUNT_MISMATCH",
                expected_amount=Decimal("100.00"),
                actual_amount=Decimal("90.00"),
                difference=Decimal("10.00"),
                match_method="PAYMENT_ID",
                match_confidence=Decimal("1.0000"),
            ),
            ReconciliationResult(
                run_id="RUN_001",
                transaction_id="pay_302",
                status="AMOUNT_MISMATCH",
                expected_amount=Decimal("200.00"),
                actual_amount=Decimal("225.00"),
                difference=Decimal("-25.00"),
                match_method="PAYMENT_ID",
                match_confidence=Decimal("1.0000"),
            ),
            ReconciliationResult(
                run_id="RUN_001",
                transaction_id="pay_303",
                status="MATCHED",
                expected_amount=Decimal("500.00"),
                actual_amount=Decimal("500.00"),
                difference=Decimal("0.00"),
                match_method="PAYMENT_ID",
                match_confidence=Decimal("1.0000"),
            ),
        ]
    )

    db.commit()

    result = get_exception_analytics(db)

    assert result["financial_exposure"] == "35.00"