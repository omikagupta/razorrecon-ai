import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal
from app.services.reconciliation.engine import (
    run_payment_settlement_reconciliation,
)
from app.services.reconciliation.persistence import (
    persist_reconciliation_results,
)


def main():
    db = SessionLocal()

    try:
        results = run_payment_settlement_reconciliation(db)

        run = persist_reconciliation_results(
            db,
            results,
        )

        print("===== RECONCILIATION PERSISTED =====")
        print(f"Run ID:        {run.run_id}")
        print(f"Total records: {run.total_records}")
        print(f"Matched:       {run.matched_records}")
        print(f"Exceptions:    {run.exception_count}")
        print(f"Status:        {run.status}")

    finally:
        db.close()


if __name__ == "__main__":
    main()