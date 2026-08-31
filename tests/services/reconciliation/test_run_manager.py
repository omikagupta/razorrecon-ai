from decimal import Decimal

from app.models.reconciliation import (
    ReconciliationResult,
)
from app.services.reconciliation.run_manager import (
    create_reconciliation_run,
    mark_run_running,
    complete_reconciliation_run,
    fail_reconciliation_run,
    get_reconciliation_run,
    list_reconciliation_runs,
    get_reconciliation_run_details,
)


def test_create_reconciliation_run(db):
    run = create_reconciliation_run(
        db=db,
        total_records=10,
    )

    assert run.run_id.startswith("RUN_")
    assert run.status == "CREATED"
    assert run.total_records == 10
    assert run.matched_records == 0
    assert run.exception_count == 0
    assert run.completed_at is None


def test_reconciliation_run_lifecycle(db):
    run = create_reconciliation_run(
        db=db,
        total_records=5,
    )

    assert run.status == "CREATED"

    run = mark_run_running(
        db=db,
        run=run,
    )

    assert run.status == "RUNNING"
    assert run.started_at is not None

    run = complete_reconciliation_run(
        db=db,
        run=run,
        total_records=5,
        matched_records=3,
        exception_count=2,
    )

    assert run.status == "COMPLETED"
    assert run.total_records == 5
    assert run.matched_records == 3
    assert run.exception_count == 2
    assert run.completed_at is not None


def test_fail_reconciliation_run(db):
    run = create_reconciliation_run(
        db=db,
        total_records=3,
    )

    run = mark_run_running(
        db=db,
        run=run,
    )

    run = fail_reconciliation_run(
        db=db,
        run=run,
    )

    assert run.status == "FAILED"
    assert run.completed_at is not None


def test_get_reconciliation_run(db):
    run = create_reconciliation_run(
        db=db,
        total_records=2,
    )

    db.commit()

    retrieved = get_reconciliation_run(
        db=db,
        run_id=run.run_id,
    )

    assert retrieved is not None
    assert retrieved.run_id == run.run_id
    assert retrieved.status == "CREATED"


def test_get_missing_reconciliation_run(db):
    result = get_reconciliation_run(
        db=db,
        run_id="RUN_DOES_NOT_EXIST",
    )

    assert result is None


def test_list_reconciliation_runs(db):
    run1 = create_reconciliation_run(
        db=db,
        total_records=1,
    )

    run2 = create_reconciliation_run(
        db=db,
        total_records=2,
    )

    db.commit()

    runs = list_reconciliation_runs(db)

    assert len(runs) >= 2
    assert runs[0].id > runs[1].id


def test_reconciliation_run_details(db):
    run = create_reconciliation_run(
        db=db,
        total_records=3,
    )

    mark_run_running(
        db=db,
        run=run,
    )

    db.add_all(
        [
            ReconciliationResult(
                run_id=run.run_id,
                transaction_id="PAY_001",
                status="MATCHED",
                expected_amount=Decimal("100.00"),
                actual_amount=Decimal("100.00"),
                difference=Decimal("0.00"),
                match_method="PAYMENT_ID",
                match_confidence=Decimal("1.0000"),
            ),
            ReconciliationResult(
                run_id=run.run_id,
                transaction_id="PAY_002",
                status="AMOUNT_MISMATCH",
                expected_amount=Decimal("200.00"),
                actual_amount=Decimal("190.00"),
                difference=Decimal("10.00"),
                match_method="PAYMENT_ID",
                match_confidence=Decimal("1.0000"),
            ),
            ReconciliationResult(
                run_id=run.run_id,
                transaction_id="PAY_003",
                status="MISSING_SETTLEMENT",
                expected_amount=Decimal("300.00"),
                actual_amount=None,
                difference=None,
                match_method="PAYMENT_ID",
                match_confidence=Decimal("1.0000"),
            ),
        ]
    )

    db.commit()

    details = get_reconciliation_run_details(
        db=db,
        run_id=run.run_id,
    )

    assert details is not None

    assert details["run"]["run_id"] == run.run_id
    assert details["run"]["status"] == "RUNNING"

    assert details["summary"]["total_results"] == 3
    assert details["summary"]["matched"] == 1
    assert details["summary"]["amount_mismatch"] == 1
    assert details["summary"]["missing_settlement"] == 1

    assert (
        details["summary"]["total_financial_difference"]
        == "10.00"
    )

    assert len(details["results"]) == 3


def test_get_missing_run_details(db):
    details = get_reconciliation_run_details(
        db=db,
        run_id="RUN_DOES_NOT_EXIST",
    )

    assert details is None