from decimal import Decimal
from datetime import UTC, datetime

from app.models.financial import (
    Adjustment,
    Fee,
    Order,
    Payment,
    Refund,
    Settlement,
)
from app.models.reconciliation import Evidence, ExceptionRecord
from app.services.reconciliation.evidence import generate_evidence


def create_exception(db, transaction_id="pay_001"):
    exception = ExceptionRecord(
        exception_id="EXC_TEST_001",
        transaction_id=transaction_id,
        exception_type="AMOUNT_MISMATCH",
        severity="HIGH",
        status="OPEN",
        confidence=Decimal("1.0000"),
    )

    db.add(exception)
    db.commit()

    return exception


def create_payment(db, payment_id="pay_001", order_id="ord_001"):
    payment = Payment(
        payment_id=payment_id,
        order_id=order_id,
        merchant_id="merch_001",
        amount=Decimal("100.00"),
        currency="INR",
        status="SUCCESS",
        payment_timestamp=datetime.now(UTC),
    )

    db.add(payment)
    db.commit()

    return payment


def test_no_payment_returns_zero(db):
    exception = create_exception(db, "missing_payment")

    count = generate_evidence(
        db=db,
        exception=exception,
    )

    assert count == 0

    evidence = (
        db.query(Evidence)
        .filter(Evidence.exception_id == exception.exception_id)
        .all()
    )

    assert evidence == []


def test_payment_evidence_created(db):
    create_payment(db)
    exception = create_exception(db)

    count = generate_evidence(
        db=db,
        exception=exception,
    )

    assert count == 1

    db.flush()

    evidence = (
        db.query(Evidence)
        .filter(Evidence.exception_id == exception.exception_id)
        .all()
    )

    assert len(evidence) == 1
    assert evidence[0].evidence_type == "PAYMENT"
    assert evidence[0].source_table == "payments"
    assert evidence[0].source_record_id == "pay_001"


def test_order_and_settlement_evidence_created(db):
    create_payment(db)

    db.add(
        Order(
            order_id="ord_001",
            merchant_id="merch_001",
            amount=Decimal("100.00"),
            currency="INR",
            status="PAID",
        )
    )

    db.add(
        Settlement(
            settlement_id="set_001",
            payment_id="pay_001",
            merchant_id="merch_001",
            amount=Decimal("100.00"),
            currency="INR",
            settlement_timestamp=datetime.now(UTC),
        )
    )

    db.commit()

    exception = create_exception(db)

    count = generate_evidence(
        db=db,
        exception=exception,
    )

    assert count == 3

    db.flush()

    evidence_types = {
        evidence.evidence_type
        for evidence in db.query(Evidence)
        .filter(Evidence.exception_id == exception.exception_id)
        .all()
    }

    assert evidence_types == {
        "PAYMENT",
        "ORDER",
        "SETTLEMENT",
    }


def test_refund_fee_and_adjustment_evidence_created(db):
    create_payment(db)

    db.add(
        Refund(
            refund_id="ref_001",
            payment_id="pay_001",
            order_id="ord_001",
            amount=Decimal("20.00"),
            status="PROCESSED",
            refund_timestamp=datetime.now(UTC)
        )
    )

    db.add(
        Fee(
            fee_id="fee_001",
            payment_id="pay_001",
            fee_type="PROCESSING",
            amount=Decimal("2.00"),
        )
    )

    db.add(
        Adjustment(
            adjustment_id="adj_001",
            payment_id="pay_001",
            adjustment_type="CREDIT",
            amount=Decimal("5.00"),
        )
    )

    db.commit()

    exception = create_exception(db)

    count = generate_evidence(
        db=db,
        exception=exception,
    )

    assert count == 4

    db.flush()

    evidence_types = [
        evidence.evidence_type
        for evidence in db.query(Evidence)
        .filter(Evidence.exception_id == exception.exception_id)
        .all()
    ]

    assert "PAYMENT" in evidence_types
    assert "REFUND" in evidence_types
    assert "FEE" in evidence_types
    assert "ADJUSTMENT" in evidence_types


def test_multiple_financial_records_generate_multiple_evidence(db):
    create_payment(db)

    db.add_all(
        [
            Refund(
                refund_id="ref_001",
                payment_id="pay_001",
                order_id="ord_001",
                amount=Decimal("10.00"),
                status="PROCESSED",
                refund_timestamp=datetime.now(UTC),
            ),
            Refund(
                refund_id="ref_002",
                payment_id="pay_001",
                order_id="ord_001",
                amount=Decimal("5.00"),
                status="PROCESSED",
                refund_timestamp=datetime.now(UTC),
            ),
            Fee(
                fee_id="fee_001",
                payment_id="pay_001",
                fee_type="PROCESSING",
                amount=Decimal("2.00"),
            ),
            Fee(
                fee_id="fee_002",
                payment_id="pay_001",
                fee_type="TAX",
                amount=Decimal("1.00"),
            ),
            Adjustment(
                adjustment_id="adj_001",
                payment_id="pay_001",
                adjustment_type="CREDIT",
                amount=Decimal("3.00"),
            ),
            Adjustment(
                adjustment_id="adj_002",
                payment_id="pay_001",
                adjustment_type="DEBIT",
                amount=Decimal("1.00"),
            ),
        ]
    )

    db.commit()

    exception = create_exception(db)

    count = generate_evidence(
        db=db,
        exception=exception,
    )

    # 1 payment + 2 refunds + 2 fees + 2 adjustments
    assert count == 7

    db.flush()

    evidence = (
        db.query(Evidence)
        .filter(Evidence.exception_id == exception.exception_id)
        .all()
    )

    assert len(evidence) == 7