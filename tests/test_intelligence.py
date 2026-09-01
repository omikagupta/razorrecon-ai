
from datetime import datetime
from decimal import Decimal

from app.models.financial import (
    Adjustment,
    Fee,
    Payment,
    Settlement,
)
from app.models.reconciliation import ExceptionRecord
from app.services.reconciliation.intelligence import (
    analyze_all_exceptions,
    analyze_exception,
)


def create_payment(
    db,
    payment_id="pay_001",
    amount=Decimal("1000.00"),
):
    payment = Payment(
        payment_id=payment_id,
        order_id=f"order_{payment_id}",
        merchant_id="merchant_001",
        amount=amount,
        currency="INR",
        status="SUCCESS",
        payment_timestamp=datetime.now(),
    )

    db.add(payment)
    db.commit()

    return payment


def create_settlement(
    db,
    payment_id="pay_001",
    amount=Decimal("1000.00"),
):
    settlement = Settlement(
        settlement_id=f"set_{payment_id}",
        payment_id=payment_id,
        merchant_id="merchant_001",
        amount=amount,
        currency="INR",
        settlement_timestamp=datetime.now(),
    )

    db.add(settlement)
    db.commit()

    return settlement


def create_exception(
    db,
    exception_id="EXC_001",
    transaction_id="pay_001",
    exception_type="AMOUNT_MISMATCH",
):
    exception = ExceptionRecord(
        exception_id=exception_id,
        transaction_id=transaction_id,
        exception_type=exception_type,
        severity="HIGH",
        status="OPEN",
        confidence=Decimal("1.0000"),
        description="Test exception",
        created_at=datetime.now(),
    )

    db.add(exception)
    db.commit()

    return exception


def create_fee(
    db,
    payment_id="pay_001",
    fee_id="fee_001",
    fee_type="PROCESSING_FEE",
    amount=Decimal("30.00"),
):
    fee = Fee(
        fee_id=fee_id,
        payment_id=payment_id,
        fee_type=fee_type,
        amount=amount,
    )

    db.add(fee)
    db.commit()

    return fee

def create_adjustment(
    db,
    payment_id="pay_001",
    adjustment_id="adj_001",
    adjustment_type="ADJUSTMENT",
    amount=Decimal("20.00"),
):
    adjustment = Adjustment(
        adjustment_id=adjustment_id,
        payment_id=payment_id,
        adjustment_type=adjustment_type,
        amount=amount,
    )

    db.add(adjustment)
    db.commit()

    return adjustment


def test_intelligence_function_exists():
    assert callable(analyze_exception)


def test_payment_not_found_returns_unknown(db):
    exception = create_exception(
        db,
        exception_id="EXC_MISSING_PAYMENT",
        transaction_id="pay_missing",
    )

    result = analyze_exception(
        db=db,
        exception=exception,
    )

    assert result["exception_id"] == "EXC_MISSING_PAYMENT"
    assert result["classification"] == "UNKNOWN"
    assert result["severity"] == "CRITICAL"
    assert result["confidence"] == Decimal("0.9900")
    assert result["recommended_action"] == "HUMAN_REVIEW"
    assert "could not be found" in result["root_cause"]


def test_missing_settlement_returns_human_review(db):
    create_payment(db)

    exception = create_exception(
        db,
        exception_id="EXC_MISSING_SETTLEMENT",
        exception_type="MISSING_SETTLEMENT",
    )

    result = analyze_exception(
        db=db,
        exception=exception,
    )

    assert result["classification"] == "MISSING_SETTLEMENT"
    assert result["severity"] == "HIGH"
    assert result["confidence"] == Decimal("0.9900")
    assert result["recommended_action"] == "HUMAN_REVIEW"
    assert "no corresponding settlement" in result["root_cause"]


def test_fee_explains_amount_mismatch(db):
    create_payment(
        db,
        amount=Decimal("1000.00"),
    )

    create_settlement(
        db,
        amount=Decimal("970.00"),
    )

    create_fee(
        db,
        amount=Decimal("30.00"),
    )

    exception = create_exception(
        db,
        exception_id="EXC_FEE",
        exception_type="AMOUNT_MISMATCH",
    )

    result = analyze_exception(
        db=db,
        exception=exception,
    )

    assert result["classification"] == "FEE_EXPLAINED_MISMATCH"
    assert result["severity"] == "LOW"
    assert result["confidence"] == Decimal("0.9800")
    assert result["recommended_action"] == "AUTO_RESOLVE"
    assert "processing fee" in result["root_cause"]


def test_fee_and_adjustment_explain_amount_mismatch(db):
    create_payment(
        db,
        amount=Decimal("1000.00"),
    )

    create_settlement(
        db,
        amount=Decimal("950.00"),
    )

    create_fee(
        db,
        amount=Decimal("30.00"),
    )

    create_adjustment(
        db,
        amount=Decimal("20.00"),
    )

    exception = create_exception(
        db,
        exception_id="EXC_FEE_ADJUSTMENT",
        exception_type="AMOUNT_MISMATCH",
    )

    result = analyze_exception(
        db=db,
        exception=exception,
    )

    assert result["classification"] == (
        "FEE_ADJUSTMENT_EXPLAINED_MISMATCH"
    )
    assert result["severity"] == "LOW"
    assert result["confidence"] == Decimal("0.9700")
    assert result["recommended_action"] == "AUTO_RESOLVE"
    assert "fees" in result["root_cause"]
    assert "adjustments" in result["root_cause"]


def test_unexplained_amount_mismatch_requires_human_review(db):
    create_payment(
        db,
        amount=Decimal("1000.00"),
    )

    create_settlement(
        db,
        amount=Decimal("900.00"),
    )

    create_fee(
        db,
        amount=Decimal("30.00"),
    )

    exception = create_exception(
        db,
        exception_id="EXC_UNEXPLAINED",
        exception_type="AMOUNT_MISMATCH",
    )

    result = analyze_exception(
        db=db,
        exception=exception,
    )

    assert result["classification"] == (
        "UNEXPLAINED_AMOUNT_MISMATCH"
    )
    assert result["severity"] == "HIGH"
    assert result["confidence"] == Decimal("0.9500")
    assert result["recommended_action"] == "HUMAN_REVIEW"
    assert "unexplained difference" in result["root_cause"]


def test_unknown_exception_type_returns_unknown(db):
    create_payment(db)

    exception = create_exception(
        db,
        exception_id="EXC_UNKNOWN",
        exception_type="SOME_FUTURE_EXCEPTION",
    )

    result = analyze_exception(
        db=db,
        exception=exception,
    )

    assert result["classification"] == "UNKNOWN"
    assert result["severity"] == "MEDIUM"
    assert result["confidence"] == Decimal("0.5000")
    assert result["recommended_action"] == "HUMAN_REVIEW"
    assert "No intelligence rule exists" in result["root_cause"]


def test_analyze_all_exceptions(db):
    create_payment(
        db,
        payment_id="pay_001",
    )

    create_settlement(
        db,
        payment_id="pay_001",
        amount=Decimal("1000.00"),
    )

    create_exception(
        db,
        exception_id="EXC_001",
        transaction_id="pay_001",
        exception_type="AMOUNT_MISMATCH",
    )

    results = analyze_all_exceptions(db)

    assert len(results) == 1
    assert results[0]["exception_id"] == "EXC_001"
    assert results[0]["classification"] == (
        "UNEXPLAINED_AMOUNT_MISMATCH"
    )


def test_decimal_difference():
    payment = Decimal("1000.00")
    settlement = Decimal("900.00")

    difference = payment - settlement

    assert difference == Decimal("100.00")


def test_fee_difference_logic():
    payment_amount = Decimal("1000.00")
    settlement_amount = Decimal("970.00")
    fee_amount = Decimal("30.00")

    difference = payment_amount - settlement_amount

    assert difference == fee_amount


def test_fee_plus_adjustment_difference_logic():
    payment_amount = Decimal("1000.00")
    settlement_amount = Decimal("950.00")
    fee_amount = Decimal("30.00")
    adjustment_amount = Decimal("20.00")

    difference = payment_amount - settlement_amount

    assert difference == fee_amount + adjustment_amount


def test_unexplained_difference_logic():
    payment_amount = Decimal("1000.00")
    settlement_amount = Decimal("900.00")
    fee_amount = Decimal("30.00")

    difference = payment_amount - settlement_amount

    assert difference != fee_amount

