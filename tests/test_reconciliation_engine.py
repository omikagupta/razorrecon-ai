
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
    currency="INR",
):
    payment = Payment(
        payment_id=payment_id,
        order_id=order_id,
        merchant_id=merchant_id,
        amount=Decimal(amount),
        currency=currency,
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
    currency="INR",
):
    settlement = Settlement(
        settlement_id=settlement_id,
        payment_id=payment_id,
        merchant_id=merchant_id,
        amount=Decimal(amount),
        currency=currency,
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
    assert result["difference"] == Decimal("0.00")
    assert result["payment_currency"] == "INR"
    assert result["settlement_currency"] == "INR"
    assert result["status"] == "MATCHED"
    assert result["match_method"] == "PAYMENT_ID"
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
    assert result["difference"] == Decimal("10.00")
    assert result["status"] == "AMOUNT_MISMATCH"
    assert result["match_method"] == "PAYMENT_ID"
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
    assert result["difference"] is None
    assert result["payment_currency"] == "INR"
    assert result["settlement_currency"] is None
    assert result["status"] == "MISSING_SETTLEMENT"
    assert result["match_method"] == "PAYMENT_ID"
    assert result["settlement_id"] is None


def test_reconcile_payment_currency_mismatch(db):
    payment = create_payment(
        db,
        payment_id="PAY_004",
        amount="100.00",
        currency="INR",
    )

    create_settlement(
        db,
        settlement_id="SET_004",
        payment_id="PAY_004",
        amount="100.00",
        currency="USD",
    )

    result = reconcile_payment(
        db=db,
        payment=payment,
    )

    assert result["payment_id"] == "PAY_004"
    assert result["payment_amount"] == Decimal("100.00")
    assert result["settlement_amount"] == Decimal("100.00")
    assert result["payment_currency"] == "INR"
    assert result["settlement_currency"] == "USD"
    assert result["difference"] is None
    assert result["status"] == "CURRENCY_MISMATCH"
    assert result["match_method"] == "PAYMENT_ID"
    assert result["settlement_id"] == "SET_004"


def test_reconcile_payment_duplicate_settlement(db):
    payment = create_payment(
        db,
        payment_id="PAY_DUP_001",
        amount="100.00",
    )

    create_settlement(
        db,
        settlement_id="SET_DUP_001",
        payment_id="PAY_DUP_001",
        amount="100.00",
    )

    create_settlement(
        db,
        settlement_id="SET_DUP_002",
        payment_id="PAY_DUP_001",
        amount="100.00",
    )

    result = reconcile_payment(
        db=db,
        payment=payment,
    )

    assert result["payment_id"] == "PAY_DUP_001"
    assert result["status"] == "DUPLICATE_SETTLEMENT"
    assert result["settlement_id"] is None
    assert result["settlement_count"] == 2

    assert set(result["settlement_ids"]) == {
        "SET_DUP_001",
        "SET_DUP_002",
    }

    assert result["settlement_amounts"] == [
        Decimal("100.00"),
        Decimal("100.00"),
    ]


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


def test_reconciliation_summary():
    results = [
        {
            "payment_id": "PAY_001",
            "status": "MATCHED",
        },
        {
            "payment_id": "PAY_002",
            "status": "AMOUNT_MISMATCH",
        },
        {
            "payment_id": "PAY_003",
            "status": "MISSING_SETTLEMENT",
        },
        {
            "payment_id": "PAY_004",
            "status": "MATCHED",
        },
        {
            "payment_id": "PAY_005",
            "status": "CURRENCY_MISMATCH",
        },
        {
            "payment_id": "PAY_006",
            "status": "DUPLICATE_SETTLEMENT",
        },
    ]

    summary = reconciliation_summary(results)

    assert summary == {
        "total": 6,
        "matched": 2,
        "amount_mismatch": 1,
        "missing_settlement": 1,
        "currency_mismatch": 1,
        "duplicate_settlement": 1,
    }


def test_reconciliation_summary_empty_results():
    summary = reconciliation_summary([])

    assert summary == {
        "total": 0,
        "matched": 0,
        "amount_mismatch": 0,
        "missing_settlement": 0,
        "currency_mismatch": 0,
        "duplicate_settlement": 0,
    }


def test_reconciliation_summary_only_currency_mismatch():
    results = [
        {
            "payment_id": "PAY_001",
            "status": "CURRENCY_MISMATCH",
        },
        {
            "payment_id": "PAY_002",
            "status": "CURRENCY_MISMATCH",
        },
    ]

    summary = reconciliation_summary(results)

    assert summary == {
        "total": 2,
        "matched": 0,
        "amount_mismatch": 0,
        "missing_settlement": 0,
        "currency_mismatch": 2,
        "duplicate_settlement": 0,
    }


def test_reconciliation_summary_only_duplicate_settlement():
    results = [
        {
            "payment_id": "PAY_001",
            "status": "DUPLICATE_SETTLEMENT",
        },
        {
            "payment_id": "PAY_002",
            "status": "DUPLICATE_SETTLEMENT",
        },
    ]

    summary = reconciliation_summary(results)

    assert summary == {
        "total": 2,
        "matched": 0,
        "amount_mismatch": 0,
        "missing_settlement": 0,
        "currency_mismatch": 0,
        "duplicate_settlement": 2,
    }
