from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

from app.models.financial import Payment, Settlement
from app.services.reconciliation.matcher import reconcile_payment


def create_payment():
    return Payment(
        payment_id="PAY_TEST_001",
        order_id="ORD_TEST_001",
        merchant_id="MER_TEST_001",
        amount=Decimal("1000.00"),
        currency="INR",
        status="SUCCESS",
        payment_timestamp=datetime.now(),
    )


def create_settlement(amount):
    return Settlement(
        settlement_id="SET_TEST_001",
        payment_id="PAY_TEST_001",
        merchant_id="MER_TEST_001",
        amount=amount,
        currency="INR",
        settlement_timestamp=datetime.now(),
    )


def test_reconcile_payment_matched():
    db = MagicMock()
    payment = create_payment()
    settlement = create_settlement(Decimal("1000.00"))

    db.query.return_value.filter.return_value.first.return_value = settlement

    result = reconcile_payment(db=db, payment=payment)

    assert result["status"] == "MATCHED"
    assert result["payment_id"] == "PAY_TEST_001"
    assert result["settlement_id"] == "SET_TEST_001"
    assert result["payment_amount"] == Decimal("1000.00")
    assert result["settlement_amount"] == Decimal("1000.00")


def test_reconcile_payment_amount_mismatch():
    db = MagicMock()
    payment = create_payment()
    settlement = create_settlement(Decimal("970.00"))

    db.query.return_value.filter.return_value.first.return_value = settlement

    result = reconcile_payment(db=db, payment=payment)

    assert result["status"] == "AMOUNT_MISMATCH"
    assert result["payment_id"] == "PAY_TEST_001"
    assert result["settlement_id"] == "SET_TEST_001"
    assert result["payment_amount"] == Decimal("1000.00")
    assert result["settlement_amount"] == Decimal("970.00")


def test_reconcile_payment_missing_settlement():
    db = MagicMock()
    payment = create_payment()

    db.query.return_value.filter.return_value.first.return_value = None

    result = reconcile_payment(db=db, payment=payment)

    assert result["status"] == "MISSING_SETTLEMENT"
    assert result["payment_id"] == "PAY_TEST_001"
    assert result["settlement_id"] is None
    assert result["payment_amount"] == Decimal("1000.00")
    assert result["settlement_amount"] is None