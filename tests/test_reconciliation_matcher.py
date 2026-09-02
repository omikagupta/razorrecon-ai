from datetime import datetime
from decimal import Decimal

from app.models.financial import Payment, Settlement
from app.services.reconciliation.matcher import reconcile_payment


def create_payment(
    db,
    payment_id="PAY_001",
    amount=Decimal("100.00"),
):
    payment = Payment(
        payment_id=payment_id,
        order_id="ORDER_001",
        merchant_id="MERCHANT_001",
        amount=Decimal(str(amount)),
        currency="INR",
        status="SUCCESS",
        payment_timestamp=datetime.now(),
    )
    db.add(payment)
    db.commit()
    return payment


def create_settlement(
    db,
    payment_id="PAY_001",
    settlement_id="SET_001",
    amount=Decimal("100.00"),
):
    settlement = Settlement(
        settlement_id=settlement_id,
        payment_id=payment_id,
        merchant_id="MERCHANT_001",
        amount=Decimal(str(amount)),
        currency="INR",
        settlement_timestamp=datetime.now(),
    )
    db.add(settlement)
    db.commit()
    return settlement


def test_reconcile_payment_duplicate_settlement(db):
    payment = create_payment(
        db,
        payment_id="PAY_DUP_001",
        amount=Decimal("100.00"),
    )

    create_settlement(
        db,
        settlement_id="SET_DUP_001",
        payment_id="PAY_DUP_001",
        amount=Decimal("100.00"),
    )

    create_settlement(
        db,
        settlement_id="SET_DUP_002",
        payment_id="PAY_DUP_001",
        amount=Decimal("100.00"),
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