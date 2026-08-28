import os
import sys

# Add backend/ to Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from app.db.session import SessionLocal
from app.services.reconciliation.engine import (
    reconciliation_summary,
    run_payment_settlement_reconciliation,
)


def main():
    db = SessionLocal()

    try:
        results = run_payment_settlement_reconciliation(db)

        summary = reconciliation_summary(results)

        print("\n===== RAZORRECON RECONCILIATION =====")
        print(f"Total Payments:       {summary['total']}")
        print(f"Matched:               {summary['matched']}")
        print(f"Amount Mismatch:       {summary['amount_mismatch']}")
        print(f"Missing Settlement:    {summary['missing_settlement']}")

        print("\n===== SAMPLE RESULTS =====")

        for result in results[:10]:
            print(
                f"{result['payment_id']} | "
                f"{result['status']} | "
                f"Payment: {result['payment_amount']} | "
                f"Settlement: {result['settlement_amount']}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()