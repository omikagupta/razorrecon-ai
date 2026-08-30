import sys
from pathlib import Path

# Add backend/ to Python path
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.db.base import Base
from app.db.session import engine

# Import all models so SQLAlchemy registers them with Base.metadata
from app.models.financial import (
    Adjustment,
    Fee,
    Order,
    Payment,
    Refund,
    Settlement,
)

from app.models.reconciliation import (
    AuditLog,
    Evidence,
    ExceptionRecord,
    HumanReview,
    ReconciliationResult,
    ReconciliationRun,
)


def main():
    Base.metadata.create_all(bind=engine)

    print("======================================")
    print("RAZORRECON DATABASE INITIALIZED")
    print("======================================")
    print()

    for table_name in sorted(Base.metadata.tables.keys()):
        print(f"Created/verified table: {table_name}")

    print()
    print("Database initialization completed.")


if __name__ == "__main__":
    main()