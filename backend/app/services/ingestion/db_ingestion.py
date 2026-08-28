from sqlalchemy.orm import Session

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


def ingest_transactions(
    db: Session,
    transactions: list[TransactionRecord],
) -> int:

    # ---------------------------------------------------------
    # 1. Remove invalid transactions
    # ---------------------------------------------------------
    valid_transactions = [
        t for t in transactions
        if t.order_id and t.order_id.strip()
    ]

    # ---------------------------------------------------------
    # 2. Load existing IDs from database
    # ---------------------------------------------------------
    existing_order_ids = {
        row[0]
        for row in db.query(Order.order_id).all()
        if row[0]
    }

    existing_payment_ids = {
        row[0]
        for row in db.query(Payment.payment_id).all()
        if row[0]
    }

    existing_settlement_ids = {
        row[0]
        for row in db.query(Settlement.settlement_id).all()
        if row[0]
    }

    existing_refund_ids = {
        row[0]
        for row in db.query(Refund.refund_id).all()
        if row[0]
    }

    existing_fee_ids = {
        row[0]
        for row in db.query(Fee.fee_id).all()
        if row[0]
    }

    existing_adjustment_ids = {
        row[0]
        for row in db.query(Adjustment.adjustment_id).all()
        if row[0]
    }

    # ---------------------------------------------------------
    # 3. Load existing merchants
    # ---------------------------------------------------------
    existing_merchants = {
        row[0]
        for row in db.query(Merchant.merchant_id).all()
        if row[0]
    }

    merchants_added = set(existing_merchants)

    inserted_count = 0

    # ---------------------------------------------------------
    # 4. Process transactions
    # ---------------------------------------------------------
    for transaction in valid_transactions:

        order_id = transaction.order_id.strip()

        # -----------------------------------------------------
        # Skip duplicate order
        # -----------------------------------------------------
        if order_id in existing_order_ids:
            continue

        # -----------------------------------------------------
        # Merchant
        # -----------------------------------------------------
        if (
            transaction.merchant_id
            and transaction.merchant_id not in merchants_added
        ):
            merchant = Merchant(
                merchant_id=transaction.merchant_id,
                name=transaction.merchant_id,
            )

            db.add(merchant)
            merchants_added.add(transaction.merchant_id)

        # -----------------------------------------------------
        # Order
        # -----------------------------------------------------
        order = Order(
            order_id=order_id,
            merchant_id=transaction.merchant_id,
            amount=transaction.payment_amount,
            currency=transaction.payment_currency,
            status=transaction.payment_status,
            created_at=transaction.payment_timestamp,
        )

        db.add(order)

        existing_order_ids.add(order_id)

        # -----------------------------------------------------
        # Payment
        # -----------------------------------------------------
        payment_id = transaction.payment_id

        if payment_id and payment_id not in existing_payment_ids:

            payment = Payment(
                payment_id=payment_id,
                order_id=order_id,
                merchant_id=transaction.merchant_id,
                amount=transaction.payment_amount,
                currency=transaction.payment_currency,
                status=transaction.payment_status,
                payment_timestamp=transaction.payment_timestamp,
            )

            db.add(payment)
            existing_payment_ids.add(payment_id)

        # -----------------------------------------------------
        # Settlement
        # -----------------------------------------------------
        settlement_id = transaction.settlement_id

        if (
            settlement_id
            and settlement_id not in existing_settlement_ids
        ):

            settlement = Settlement(
                settlement_id=settlement_id,
                payment_id=payment_id,
                merchant_id=transaction.merchant_id,
                amount=transaction.settlement_amount or 0,
                currency=(
                    transaction.settlement_currency
                    or transaction.payment_currency
                ),
                settlement_timestamp=(
                    transaction.settlement_timestamp
                    or transaction.payment_timestamp
                ),
            )

            db.add(settlement)
            existing_settlement_ids.add(settlement_id)

        # -----------------------------------------------------
        # Refund
        # -----------------------------------------------------
        refund_id = transaction.refund_id

        if refund_id and refund_id not in existing_refund_ids:

            refund = Refund(
                refund_id=refund_id,
                payment_id=payment_id,
                order_id=order_id,
                amount=transaction.refund_amount,
                status=transaction.refund_status or "UNKNOWN",
                refund_timestamp=transaction.payment_timestamp,
            )

            db.add(refund)
            existing_refund_ids.add(refund_id)

        # -----------------------------------------------------
        # Fee
        # -----------------------------------------------------
        fee_id = transaction.fee_id

        if fee_id and fee_id not in existing_fee_ids:

            fee = Fee(
                fee_id=fee_id,
                payment_id=payment_id,
                fee_type=transaction.fee_type or "UNKNOWN",
                amount=transaction.fee_amount,
                created_at=transaction.payment_timestamp,
            )

            db.add(fee)
            existing_fee_ids.add(fee_id)

        # -----------------------------------------------------
        # Adjustment
        # -----------------------------------------------------
        adjustment_id = transaction.adjustment_id

        if (
            adjustment_id
            and adjustment_id not in existing_adjustment_ids
        ):

            adjustment = Adjustment(
                adjustment_id=adjustment_id,
                payment_id=payment_id,
                adjustment_type="TRANSACTION_ADJUSTMENT",
                amount=transaction.adjustment_amount,
                created_at=transaction.payment_timestamp,
            )

            db.add(adjustment)
            existing_adjustment_ids.add(adjustment_id)

        inserted_count += 1

    # ---------------------------------------------------------
    # 5. Commit everything
    # ---------------------------------------------------------
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return inserted_count