from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.reconciliation.engine import (
    reconciliation_summary,
    run_payment_settlement_reconciliation,
)


def test_run_payment_settlement_reconciliation():
    db = MagicMock()

    payment_1 = MagicMock()
    payment_1.id = 1
    payment_1.payment_id = "PAY_001"

    payment_2 = MagicMock()
    payment_2.id = 2
    payment_2.payment_id = "PAY_002"

    db.query.return_value.order_by.return_value.all.return_value = [
        payment_1,
        payment_2,
    ]

    expected_results = [
        {
            "payment_id": "PAY_001",
            "status": "MATCHED",
        },
        {
            "payment_id": "PAY_002",
            "status": "AMOUNT_MISMATCH",
        },
    ]

    with patch(
        "app.services.reconciliation.engine.reconcile_payment",
        side_effect=expected_results,
    ) as mock_reconcile:
        results = run_payment_settlement_reconciliation(db)

    assert results == expected_results

    assert mock_reconcile.call_count == 2
    mock_reconcile.assert_any_call(
        db=db,
        payment=payment_1,
    )
    mock_reconcile.assert_any_call(
        db=db,
        payment=payment_2,
    )


def test_run_payment_settlement_reconciliation_no_payments():
    db = MagicMock()

    db.query.return_value.order_by.return_value.all.return_value = []

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
    ]

    summary = reconciliation_summary(results)

    assert summary == {
        "total": 4,
        "matched": 2,
        "amount_mismatch": 1,
        "missing_settlement": 1,
    }


def test_reconciliation_summary_empty_results():
    summary = reconciliation_summary([])

    assert summary == {
        "total": 0,
        "matched": 0,
        "amount_mismatch": 0,
        "missing_settlement": 0,
    }