import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal
from app.models.reconciliation import ExceptionRecord
from app.services.reconciliation.evidence import generate_evidence


def main():
    db = SessionLocal()

    try:
        exceptions = (
            db.query(ExceptionRecord)
            .all()
        )

        total_evidence = 0

        for exception in exceptions:
            count = generate_evidence(
                db,
                exception,
            )
            total_evidence += count

        db.commit()

        print("===== EVIDENCE GENERATION =====")
        print(f"Exceptions processed: {len(exceptions)}")
        print(f"Evidence created:     {total_evidence}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()