from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.financial import (
    Adjustment,
    Fee,
    Merchant,
    Order,
    Payment,
    Refund,
    Settlement,
)
from app.services.ingestion.csv_ingestion import TransactionRecord
from app.services.ingestion.db_ingestion import ingest_transactions


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def make_transaction(
    *,
    order_id="order_001",
    payment_id="pay_001",
    merchant_id="merchant_001",
    settlement_id="set_001",
    refund_id="refund_001",
    fee_id="fee_001",
    adjustment_id="adj_001",
):
    timestamp = datetime.now(UTC)

    return TransactionRecord(
        transaction_id="txn_001",
        merchant_id=merchant_id,
        order_id=order_id,
        payment_id=payment_id,
        payment_status="CAPTURED",
        payment_amount=Decimal("1000.00"),
        payment_currency="INR",
        payment_timestamp=timestamp,
        settlement_id=settlement_id,
        settlement_amount=Decimal("1000.00"),
        settlement_currency="INR",
        settlement_timestamp=timestamp,
        fee_id=fee_id,
        fee_amount=Decimal("20.00"),
        fee_type="PROCESSING",
        tax_amount=Decimal("3.60"),
        refund_id=refund_id,
        refund_amount=Decimal("0.00"),
        refund_status="NONE",
        adjustment_id=adjustment_id,
        adjustment_amount=Decimal("0.00"),
        scenario_type="MATCHED",
        ground_truth="MATCHED",
    )


def test_complete_transaction_is_inserted(db):
    transaction = make_transaction()

    inserted = ingest_transactions(db, [transaction])

    assert inserted == 1

    assert db.query(Merchant).count() == 1
    assert db.query(Order).count() == 1
    assert db.query(Payment).count() == 1
    assert db.query(Settlement).count() == 1
    assert db.query(Refund).count() == 1
    assert db.query(Fee).count() == 1
    assert db.query(Adjustment).count() == 1


def test_invalid_order_id_is_skipped(db):
    transaction = make_transaction(order_id="   ")

    inserted = ingest_transactions(db, [transaction])

    assert inserted == 0
    assert db.query(Order).count() == 0
    assert db.query(Payment).count() == 0


def test_duplicate_order_is_skipped(db):
    transaction = make_transaction()

    first_insert = ingest_transactions(db, [transaction])
    second_insert = ingest_transactions(db, [transaction])

    assert first_insert == 1
    assert second_insert == 0

    assert db.query(Order).count() == 1
    assert db.query(Payment).count() == 1


def test_duplicate_financial_ids_are_not_inserted(db):
    first = make_transaction()

    ingest_transactions(db, [first])

    second = make_transaction(
        order_id="order_002",
        payment_id="pay_001",
        settlement_id="set_001",
        refund_id="refund_001",
        fee_id="fee_001",
        adjustment_id="adj_001",
    )

    inserted = ingest_transactions(db, [second])

    assert inserted == 1

    assert db.query(Order).count() == 2
    assert db.query(Payment).count() == 1
    assert db.query(Settlement).count() == 1
    assert db.query(Refund).count() == 1
    assert db.query(Fee).count() == 1
    assert db.query(Adjustment).count() == 1


def test_missing_settlement_does_not_create_settlement(db):
    transaction = make_transaction(
        settlement_id=None,
    )

    inserted = ingest_transactions(db, [transaction])

    assert inserted == 1
    assert db.query(Order).count() == 1
    assert db.query(Payment).count() == 1
    assert db.query(Settlement).count() == 0


def test_missing_optional_financial_records_are_allowed(db):
    transaction = make_transaction(
        settlement_id=None,
        refund_id=None,
        fee_id=None,
        adjustment_id=None,
    )

    inserted = ingest_transactions(db, [transaction])

    assert inserted == 1

    assert db.query(Merchant).count() == 1
    assert db.query(Order).count() == 1
    assert db.query(Payment).count() == 1
    assert db.query(Settlement).count() == 0
    assert db.query(Refund).count() == 0
    assert db.query(Fee).count() == 0
    assert db.query(Adjustment).count() == 0


def test_multiple_transactions_are_inserted(db):
    transactions = [
        make_transaction(
            order_id="order_001",
            payment_id="pay_001",
            settlement_id="set_001",
            refund_id=None,
            fee_id="fee_001",
            adjustment_id=None,
        ),
        make_transaction(
            order_id="order_002",
            payment_id="pay_002",
            settlement_id="set_002",
            refund_id=None,
            fee_id="fee_002",
            adjustment_id=None,
        ),
    ]

    inserted = ingest_transactions(db, transactions)

    assert inserted == 2

    assert db.query(Merchant).count() == 1
    assert db.query(Order).count() == 2
    assert db.query(Payment).count() == 2
    assert db.query(Settlement).count() == 2
    assert db.query(Fee).count() == 2


def test_different_merchants_are_created(db):
    transactions = [
        make_transaction(
            order_id="order_001",
            payment_id="pay_001",
            settlement_id=None,
            refund_id=None,
            fee_id=None,
            adjustment_id=None,
            merchant_id="merchant_001",
        ),
        make_transaction(
            order_id="order_002",
            payment_id="pay_002",
            settlement_id=None,
            refund_id=None,
            fee_id=None,
            adjustment_id=None,
            merchant_id="merchant_002",
        ),
    ]

    inserted = ingest_transactions(db, transactions)

    assert inserted == 2
    assert db.query(Merchant).count() == 2


def test_transaction_without_payment_id_can_be_inserted(db):
    transaction = make_transaction(
        payment_id=None,
        settlement_id=None,
        refund_id=None,
        fee_id=None,
        adjustment_id=None,
    )

    inserted = ingest_transactions(db, [transaction])

    assert inserted == 1
    assert db.query(Order).count() == 1
    assert db.query(Payment).count() == 0