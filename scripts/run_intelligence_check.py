
import sys
from pathlib import Path

# Add backend/ to Python path so "from app..." works
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

sys.path.insert(0, str(BACKEND))

from app.db.session import SessionLocal
from app.services.reconciliation.intelligence import analyze_all_exceptions


def main():
    db = SessionLocal()

    try:
        results = analyze_all_exceptions(db)

        print("\n===== RAZORRECON EXCEPTION INTELLIGENCE =====")
        print(f"Total exceptions analyzed: {len(results)}")

        classifications = {}

        for result in results:
            classification = result["classification"]
            classifications[classification] = (
                classifications.get(classification, 0) + 1
            )

        print("\n===== CLASSIFICATIONS =====")

        for classification, count in classifications.items():
            print(f"{classification}: {count}")

        print("\n===== SAMPLE ANALYSIS =====")

        for result in results[:10]:
            print(f"\nException: {result['exception_id']}")
            print(f"Classification: {result['classification']}")
            print(f"Severity: {result['severity']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Action: {result['recommended_action']}")
            print(f"Root Cause: {result['root_cause']}")

    finally:
        db.close()


if __name__ == "__main__":
    main()