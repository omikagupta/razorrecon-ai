from decimal import Decimal

import pytest

from app.models.financial import Payment, Settlement
from app.models.reconciliation import (
    AuditLog,
    ExceptionRecord,
    ReconciliationResult,
)
from app.services.reconciliation.persistence import (
    persist_reconciliation_results,
)


def create_payment(
    db,
    payment_id="pay_001",
    amount=Decimal("100.00"),
):
    payment = Payment(
        payment_id=payment_id,
        order_id="order_001",
        merchant_id="merchant_001",
        amount=amount,
        currency="INR",
        status="SUCCESS",
        payment_timestamp=__import__("datetime").datetime.now(),
    )

    db.add(payment)
    db.commit()

    return payment


def create_settlement(
    db,
    payment_id="pay_001",
    settlement_id="set_001",
    amount=Decimal("100.00"),
):
    settlement = Settlement(
        settlement_id=settlement_id,
        payment_id=payment_id,
        merchant_id="merchant_001",
        amount=amount,
        currency="INR",
        settlement_timestamp=__import__("datetime").datetime.now(),
    )

    db.add(settlement)
    db.commit()

    return settlement


def test_persist_matched_result(db):
    create_payment(db)
    create_settlement(db)

    results = [
        {
            "payment_id": "pay_001",
            "order_id": "order_001",
            "merchant_id": "merchant_001",
            "payment_amount": Decimal("100.00"),
            "settlement_amount": Decimal("100.00"),
            "status": "MATCHED",
            "settlement_id": "set_001",
        }
    ]

    run = persist_reconciliation_results(
        db=db,
        results=results,
    )

    assert run.status == "COMPLETED"
    assert run.total_records == 1
    assert run.matched_records == 1
    assert run.exception_count == 0

    reconciliation = (
        db.query(ReconciliationResult)
        .filter(
            ReconciliationResult.transaction_id == "pay_001"
        )
        .one()
    )

    assert reconciliation.status == "MATCHED"
    assert reconciliation.difference == Decimal("0.00")

    audit = (
        db.query(AuditLog)
        .filter(AuditLog.transaction_id == "pay_001")
        .one()
    )

    assert audit.action == "RECONCILIATION_MATCHED"
    assert audit.new_state == "MATCHED"


def test_persist_amount_mismatch_creates_exception(db):
    create_payment(
        db,
        amount=Decimal("100.00"),
    )

    create_settlement(
        db,
        amount=Decimal("95.00"),
    )

    results = [
        {
            "payment_id": "pay_001",
            "order_id": "order_001",
            "merchant_id": "merchant_001",
            "payment_amount": Decimal("100.00"),
            "settlement_amount": Decimal("95.00"),
            "status": "AMOUNT_MISMATCH",
            "settlement_id": "set_001",
        }
    ]

    run = persist_reconciliation_results(
        db=db,
        results=results,
    )

    assert run.status == "COMPLETED"
    assert run.total_records == 1
    assert run.matched_records == 0
    assert run.exception_count == 1

    exception = (
        db.query(ExceptionRecord)
        .filter(
            ExceptionRecord.transaction_id == "pay_001"
        )
        .one()
    )

    assert exception.exception_type == "AMOUNT_MISMATCH"
    assert exception.severity == "HIGH"
    assert exception.status == "OPEN"

    reconciliation = (
        db.query(ReconciliationResult)
        .filter(
            ReconciliationResult.transaction_id == "pay_001"
        )
        .one()
    )

    assert reconciliation.difference == Decimal("5.00")


def test_persist_missing_settlement_creates_exception(db):
    create_payment(db)

    results = [
        {
            "payment_id": "pay_001",
            "order_id": "order_001",
            "merchant_id": "merchant_001",
            "payment_amount": Decimal("100.00"),
            "settlement_amount": None,
            "status": "MISSING_SETTLEMENT",
            "settlement_id": None,
        }
    ]

    run = persist_reconciliation_results(
        db=db,
        results=results,
    )

    assert run.status == "COMPLETED"
    assert run.total_records == 1
    assert run.matched_records == 0
    assert run.exception_count == 1

    exception = (
        db.query(ExceptionRecord)
        .filter(
            ExceptionRecord.transaction_id == "pay_001"
        )
        .one()
    )

    assert exception.exception_type == "MISSING_SETTLEMENT"
    assert exception.severity == "CRITICAL"
    assert exception.status == "OPEN"


def test_empty_results_rejected(db):
    with pytest.raises(
        ValueError,
        match="Cannot persist an empty reconciliation result set",
    ):
        persist_reconciliation_results(
            db=db,
            results=[],
        )


def test_missing_payment_id_rejected(db):
    results = [
        {
            "payment_id": None,
            "order_id": "order_001",
            "merchant_id": "merchant_001",
            "payment_amount": Decimal("100.00"),
            "settlement_amount": Decimal("100.00"),
            "status": "MATCHED",
        }
    ]

    with pytest.raises(
        ValueError,
        match="Every reconciliation result must contain payment_id",
    ):
        persist_reconciliation_results(
            db=db,
            results=results,
        )


def test_duplicate_payment_ids_rejected(db):
    results = [
        {
            "payment_id": "pay_001",
            "status": "MATCHED",
            "payment_amount": Decimal("100.00"),
            "settlement_amount": Decimal("100.00"),
        },
        {
            "payment_id": "pay_001",
            "status": "MATCHED",
            "payment_amount": Decimal("200.00"),
            "settlement_amount": Decimal("200.00"),
        },
    ]

    with pytest.raises(
        ValueError,
        match="Duplicate payment_id detected",
    ):
        persist_reconciliation_results(
            db=db,
            results=results,
        )


def test_unsupported_status_rejected(db):
    results = [
        {
            "payment_id": "pay_001",
            "status": "UNKNOWN_STATUS",
            "payment_amount": Decimal("100.00"),
            "settlement_amount": Decimal("100.00"),
        }
    ]

    with pytest.raises(
        ValueError,
        match="Unsupported reconciliation status",
    ):
        persist_reconciliation_results(
            db=db,
            results=results,
        )
def test_persist_unsupported_status_rolls_back_run(db):
    results = [
        {
            "payment_id": "pay_001",
            "order_id": "order_001",
            "merchant_id": "merchant_001",
            "payment_amount": Decimal("100.00"),
            "settlement_amount": Decimal("100.00"),
            "status": "UNKNOWN_STATUS",
        }
    ]

    with pytest.raises(
        ValueError,
        match="Unsupported reconciliation status",
    ):
        persist_reconciliation_results(
            db=db,
            results=results,
        )

    # The failed transaction must not leave behind
    # partially persisted reconciliation data.
    assert (
        db.query(ReconciliationResult).count()
        == 0
    )

    assert (
        db.query(ExceptionRecord).count()
        == 0
    )

    assert (
        db.query(AuditLog).count()
        == 0
    )