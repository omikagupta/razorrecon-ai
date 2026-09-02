from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class FakeRun:
    def __init__(
        self,
        run_id="RUN_TEST_001",
        status="COMPLETED",
        total_records=3,
        matched_records=1,
        exception_count=2,
    ):
        self.run_id = run_id
        self.status = status
        self.total_records = total_records
        self.matched_records = matched_records
        self.exception_count = exception_count
        self.started_at = None
        self.completed_at = None


# =========================================================
# TEST 1 â€” LIST RECONCILIATION RUNS
# =========================================================

def test_list_reconciliation_runs(monkeypatch):

    fake_runs = [
        FakeRun(
            run_id="RUN_TEST_001",
        ),
        FakeRun(
            run_id="RUN_TEST_002",
        ),
    ]

    monkeypatch.setattr(
        "app.api.v1.reconciliation_runs.list_reconciliation_runs",
        lambda db: fake_runs,
    )

    response = client.get(
        "/api/v1/reconciliation-runs"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["runs"]) == 2
    assert data["runs"][0]["run_id"] == "RUN_TEST_001"


# =========================================================
# TEST 2 â€” GET RUN DETAILS
# =========================================================

def test_get_reconciliation_run_details(monkeypatch):

    fake_details = {
        "run": {
            "run_id": "RUN_TEST_001",
            "status": "COMPLETED",
            "total_records": 3,
            "matched_records": 1,
            "exception_count": 2,
            "started_at": None,
            "completed_at": None,
        },
        "summary": {
            "total_results": 3,
            "matched": 1,
            "amount_mismatch": 1,
            "missing_settlement": 1,
            "total_financial_difference": "150.00",
        },
        "status_distribution": {
            "MATCHED": 1,
            "AMOUNT_MISMATCH": 1,
            "MISSING_SETTLEMENT": 1,
        },
        "results": [],
    }

    monkeypatch.setattr(
        "app.api.v1.reconciliation_runs.get_reconciliation_run_details",
        lambda db, run_id: fake_details,
    )

    response = client.get(
        "/api/v1/reconciliation-runs/RUN_TEST_001"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["run"]["run_id"] == "RUN_TEST_001"
    assert data["summary"]["total_results"] == 3
    assert data["summary"]["matched"] == 1

    assert (
        data["summary"]["amount_mismatch"]
        == 1
    )


# =========================================================
# TEST 3 â€” RUN NOT FOUND
# =========================================================

def test_reconciliation_run_not_found(monkeypatch):

    monkeypatch.setattr(
        "app.api.v1.reconciliation_runs.get_reconciliation_run_details",
        lambda db, run_id: None,
    )

    response = client.get(
        "/api/v1/reconciliation-runs/RUN_UNKNOWN"
    )

    assert response.status_code == 404

    data = response.json()

    assert (
        data["error"]
        == "RECONCILIATION_RUN_NOT_FOUND"
    )

    assert data["run_id"] == "RUN_UNKNOWN"


# =========================================================
# TEST 4 â€” RESPONSE STRUCTURE
# =========================================================

def test_reconciliation_run_response_structure(monkeypatch):

    fake_details = {
        "run": {
            "run_id": "RUN_TEST_001",
            "status": "COMPLETED",
            "total_records": 1,
            "matched_records": 1,
            "exception_count": 0,
            "started_at": None,
            "completed_at": None,
        },
        "summary": {
            "total_results": 1,
            "matched": 1,
            "amount_mismatch": 0,
            "missing_settlement": 0,
            "total_financial_difference": "0.00",
        },
        "status_distribution": {
            "MATCHED": 1,
            "AMOUNT_MISMATCH": 0,
            "MISSING_SETTLEMENT": 0,
        },
        "results": [],
    }

    monkeypatch.setattr(
        "app.api.v1.reconciliation_runs.get_reconciliation_run_details",
        lambda db, run_id: fake_details,
    )

    response = client.get(
        "/api/v1/reconciliation-runs/RUN_TEST_001"
    )

    assert response.status_code == 200

    data = response.json()

    assert "run" in data
    assert "summary" in data
    assert "status_distribution" in data
    assert "results" in data

# =========================================================
# TEST 5 â€” RUN RECONCILIATION SUCCESS
# =========================================================

def test_run_reconciliation_success(monkeypatch):

    fake_results = [
        {
            "payment_id": "PAY_TEST_001",
            "status": "MATCHED",
            "payment_amount": "100.00",
            "settlement_amount": "100.00",
        }
    ]

    fake_run = FakeRun(
        run_id="RUN_TEST_SUCCESS",
        status="COMPLETED",
        total_records=1,
        matched_records=1,
        exception_count=0,
    )

    monkeypatch.setattr(
        "app.api.v1.reconciliation_runs.run_payment_settlement_reconciliation",
        lambda db: fake_results,
    )

    monkeypatch.setattr(
        "app.api.v1.reconciliation_runs.persist_reconciliation_results",
        lambda db, results: fake_run,
    )

    response = client.post(
        "/api/v1/reconciliation-runs"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == (
        "Reconciliation completed successfully."
    )

    assert data["run"]["run_id"] == "RUN_TEST_SUCCESS"
    assert data["run"]["status"] == "COMPLETED"
    assert data["run"]["total_records"] == 1
    assert data["run"]["matched_records"] == 1
    assert data["run"]["exception_count"] == 0


# =========================================================
# TEST 6 â€” RECONCILIATION VALIDATION ERROR
# =========================================================

def test_run_reconciliation_validation_error(monkeypatch):

    def raise_validation_error(db):
        raise ValueError(
            "Invalid reconciliation input."
        )

    monkeypatch.setattr(
        "app.api.v1.reconciliation_runs.run_payment_settlement_reconciliation",
        raise_validation_error,
    )

    response = client.post(
        "/api/v1/reconciliation-runs"
    )

    assert response.status_code == 400

    data = response.json()

    assert data["error"] == (
        "RECONCILIATION_VALIDATION_ERROR"
    )

    assert data["message"] == (
        "Invalid reconciliation input."
    )


# =========================================================
# TEST 7 â€” RECONCILIATION UNEXPECTED ERROR
# =========================================================

def test_run_reconciliation_unexpected_error(monkeypatch):

    def raise_unexpected_error(db):
        raise RuntimeError(
            "Database connection failed."
        )

    monkeypatch.setattr(
        "app.api.v1.reconciliation_runs.run_payment_settlement_reconciliation",
        raise_unexpected_error,
    )

    response = client.post(
        "/api/v1/reconciliation-runs"
    )

    assert response.status_code == 500

    data = response.json()

    assert data["error"] == (
        "RECONCILIATION_FAILED"
    )

    assert data["message"] == (
        "Database connection failed."
    )
