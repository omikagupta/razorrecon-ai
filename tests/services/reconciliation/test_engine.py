from datetime import datetime
from decimal import Decimal

from app.models.financial import Payment, Settlement
from app.services.reconciliation.engine import (
    reconciliation_summary,
    run_payment_settlement_reconciliation,
)
from app.services.reconciliation.matcher import reconcile_payment


def create_payment(
    db,
    payment_id,
    amount,
    order_id="ORDER_001",
    merchant_id="MERCHANT_001",
):
    payment = Payment(
        payment_id=payment_id,
        order_id=order_id,
        merchant_id=merchant_id,
        amount=Decimal(amount),
        currency="INR",
        status="SUCCESS",
        payment_timestamp=datetime.now(),
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


def create_settlement(
    db,
    settlement_id,
    payment_id,
    amount,
    merchant_id="MERCHANT_001",
):
    settlement = Settlement(
        settlement_id=settlement_id,
        payment_id=payment_id,
        merchant_id=merchant_id,
        amount=Decimal(amount),
        currency="INR",
        settlement_timestamp=datetime.now(),
    )

    db.add(settlement)
    db.commit()
    db.refresh(settlement)

    return settlement


def test_reconcile_payment_matched(db):
    payment = create_payment(
        db,
        payment_id="PAY_001",
        amount="100.00",
    )

    create_settlement(
        db,
        settlement_id="SET_001",
        payment_id="PAY_001",
        amount="100.00",
    )

    result = reconcile_payment(
        db=db,
        payment=payment,
    )

    assert result["payment_id"] == "PAY_001"
    assert result["payment_amount"] == Decimal("100.00")
    assert result["settlement_amount"] == Decimal("100.00")
    assert result["status"] == "MATCHED"
    assert result["settlement_id"] == "SET_001"


def test_reconcile_payment_amount_mismatch(db):
    payment = create_payment(
        db,
        payment_id="PAY_002",
        amount="100.00",
    )

    create_settlement(
        db,
        settlement_id="SET_002",
        payment_id="PAY_002",
        amount="90.00",
    )

    result = reconcile_payment(
        db=db,
        payment=payment,
    )

    assert result["payment_id"] == "PAY_002"
    assert result["payment_amount"] == Decimal("100.00")
    assert result["settlement_amount"] == Decimal("90.00")
    assert result["status"] == "AMOUNT_MISMATCH"
    assert result["settlement_id"] == "SET_002"


def test_reconcile_payment_missing_settlement(db):
    payment = create_payment(
        db,
        payment_id="PAY_003",
        amount="250.00",
    )

    result = reconcile_payment(
        db=db,
        payment=payment,
    )

    assert result["payment_id"] == "PAY_003"
    assert result["payment_amount"] == Decimal("250.00")
    assert result["settlement_amount"] is None
    assert result["status"] == "MISSING_SETTLEMENT"
    assert result["settlement_id"] is None


def test_run_payment_settlement_reconciliation(db):
    payment1 = create_payment(
        db,
        payment_id="PAY_001",
        amount="100.00",
    )

    payment2 = create_payment(
        db,
        payment_id="PAY_002",
        amount="200.00",
    )

    payment3 = create_payment(
        db,
        payment_id="PAY_003",
        amount="300.00",
    )

    create_settlement(
        db,
        settlement_id="SET_001",
        payment_id=payment1.payment_id,
        amount="100.00",
    )

    create_settlement(
        db,
        settlement_id="SET_002",
        payment_id=payment2.payment_id,
        amount="190.00",
    )

    results = run_payment_settlement_reconciliation(db)

    assert len(results) == 3

    assert results[0]["status"] == "MATCHED"
    assert results[1]["status"] == "AMOUNT_MISMATCH"
    assert results[2]["status"] == "MISSING_SETTLEMENT"


def test_run_payment_settlement_reconciliation_empty_database(db):
    results = run_payment_settlement_reconciliation(db)

    assert results == []


def test_reconciliation_summary(db):
    results = [
        {
            "status": "MATCHED",
        },
        {
            "status": "MATCHED",
        },
        {
            "status": "AMOUNT_MISMATCH",
        },
        {
            "status": "MISSING_SETTLEMENT",
        },
    ]

    summary = reconciliation_summary(results)

    assert summary == {
        "total": 4,
        "matched": 2,
        "amount_mismatch": 1,
        "missing_settlement": 1,
    }


def test_reconciliation_summary_empty():
    summary = reconciliation_summary([])

    assert summary == {
        "total": 0,
        "matched": 0,
        "amount_mismatch": 0,
        "missing_settlement": 0,
    }