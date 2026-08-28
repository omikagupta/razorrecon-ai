import sys
from pathlib import Path

# Add backend/ to Python's import path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal
from app.services.ingestion.csv_ingestion import load_transactions
from app.services.ingestion.db_ingestion import ingest_transactions


CSV_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "synthetic"
    / "transactions.csv"
)


def main() -> None:
    transactions = load_transactions(CSV_PATH)

    db = SessionLocal()

    try:
        count = ingest_transactions(db, transactions)
        print(f"Successfully ingested {count} transactions.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()