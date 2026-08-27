from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path


SEED = 42
TRANSACTION_COUNT = 500

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "synthetic"


SCENARIOS = [
    "NORMAL",
    "PROCESSING_FEE",
    "RECONCILED_TAX",
    "RECONCILED_REFUND",
    "PAYMENT_FAILED",
    "DUPLICATE_PAYMENT_ATTEMPT",
    "SETTLEMENT_DELAY",
    "RECONCILED_PARTIAL",
    "MISSING_SETTLEMENT",
    "UNEXPLAINED_DISCREPANCY",
    "UNSUPPORTED_REFUND",
    "DUPLICATE_SETTLEMENT",
    "INVALID_REFUND",
    "ORPHAN_PAYMENT",
    "ORDER_WITHOUT_PAYMENT",
]


SCENARIO_WEIGHTS = [
    0.20,  # NORMAL
    0.10,  # PROCESSING_FEE
    0.07,  # RECONCILED_TAX
    0.07,  # RECONCILED_REFUND
    0.06,  # PAYMENT_FAILED
    0.06,  # DUPLICATE_PAYMENT_ATTEMPT
    0.06,  # SETTLEMENT_DELAY
    0.06,  # RECONCILED_PARTIAL
    0.07,  # MISSING_SETTLEMENT
    0.07,  # UNEXPLAINED_DISCREPANCY
    0.05,  # UNSUPPORTED_REFUND
    0.05,  # DUPLICATE_SETTLEMENT
    0.04,  # INVALID_REFUND
    0.02,  # ORPHAN_PAYMENT
    0.02,  # ORDER_WITHOUT_PAYMENT
]


MERCHANTS = [
    ("MER_001", "Northstar Retail"),
    ("MER_002", "UrbanCart"),
    ("MER_003", "Nova Electronics"),
    ("MER_004", "GreenBasket"),
    ("MER_005", "CloudKitchen"),
    ("MER_006", "Metro Fashion"),
    ("MER_007", "QuickMart"),
    ("MER_008", "TechNest"),
]


FIELDNAMES = [
    "transaction_id",
    "merchant_id",
    "order_id",
    "payment_id",
    "payment_status",
    "payment_amount",
    "payment_currency",
    "payment_timestamp",
    "settlement_id",
    "settlement_amount",
    "settlement_currency",
    "settlement_timestamp",
    "fee_id",
    "fee_amount",
    "fee_type",
    "tax_amount",
    "refund_id",
    "refund_amount",
    "refund_status",
    "adjustment_id",
    "adjustment_amount",
    "scenario_type",
    "ground_truth",
]


def money(value: Decimal) -> str:
    return f"{value:.2f}"


def random_amount(rng: random.Random) -> Decimal:
    return Decimal(rng.randint(100, 100000)) / Decimal("1")


def random_timestamp(rng: random.Random) -> datetime:
    start = datetime(2026, 1, 1, 9, 0, 0)
    offset = rng.randint(0, 180 * 24 * 60)
    return start + timedelta(minutes=offset)


def calculate_fee(amount: Decimal) -> Decimal:
    return (amount * Decimal("0.02")).quantize(Decimal("0.01"))


def calculate_tax(fee: Decimal) -> Decimal:
    return (fee * Decimal("0.18")).quantize(Decimal("0.01"))


def build_record(
    rng: random.Random,
    index: int,
    scenario: str,
) -> dict[str, str]:

    transaction_id = f"TXN_{index:06d}"
    merchant_id, _ = rng.choice(MERCHANTS)

    order_id = f"ORD_{index:06d}"
    payment_id = f"PAY_{index:06d}"
    settlement_id = f"SET_{index:06d}"
    fee_id = f"FEE_{index:06d}"
    refund_id = f"REF_{index:06d}"
    adjustment_id = f"ADJ_{index:06d}"

    amount = random_amount(rng)
    payment_timestamp = random_timestamp(rng)

    fee = Decimal("0.00")
    tax = Decimal("0.00")
    refund = Decimal("0.00")
    settlement = amount
    settlement_timestamp = payment_timestamp + timedelta(
        days=rng.randint(1, 3)
    )

    payment_status = "SUCCESS"
    refund_status = ""

    if scenario == "NORMAL":
        pass

    elif scenario == "PROCESSING_FEE":
        fee = calculate_fee(amount)
        settlement = amount - fee

    elif scenario == "RECONCILED_TAX":
        fee = calculate_fee(amount)
        tax = calculate_tax(fee)
        settlement = amount - fee - tax

    elif scenario == "RECONCILED_REFUND":
        refund = (amount * Decimal("0.25")).quantize(Decimal("0.01"))
        refund_status = "PROCESSED"
        settlement = amount - refund

    elif scenario == "PAYMENT_FAILED":
        payment_status = "FAILED"
        settlement = Decimal("0.00")

    elif scenario == "DUPLICATE_PAYMENT_ATTEMPT":
        payment_status = "SUCCESS"

    elif scenario == "SETTLEMENT_DELAY":
        settlement_timestamp = payment_timestamp + timedelta(days=5)

    elif scenario == "RECONCILED_PARTIAL":
        refund = (amount * Decimal("0.25")).quantize(Decimal("0.01"))
        refund_status = "PROCESSED"
        settlement = amount - refund

    elif scenario == "MISSING_SETTLEMENT":
        settlement_id = ""
        settlement = Decimal("0.00")

    elif scenario == "UNEXPLAINED_DISCREPANCY":
        difference = max(
            Decimal("10.00"),
            (amount * Decimal("0.05")).quantize(Decimal("0.01")),
        )
        settlement = amount - difference

    elif scenario == "UNSUPPORTED_REFUND":
        refund = (amount * Decimal("0.20")).quantize(Decimal("0.01"))
        refund_status = "PROCESSED"

    elif scenario == "DUPLICATE_SETTLEMENT":
        settlement = amount

    elif scenario == "INVALID_REFUND":
        refund = amount * Decimal("1.40")
        refund_status = "PROCESSED"
        settlement = Decimal("0.00")

    elif scenario == "ORPHAN_PAYMENT":
        order_id = ""
        settlement = amount

    elif scenario == "ORDER_WITHOUT_PAYMENT":
        payment_id = ""
        payment_status = "MISSING"
        settlement_id = ""
        settlement = Decimal("0.00")

    expected_amount = amount - fee - tax - refund

    row = {
        "transaction_id": transaction_id,
        "merchant_id": merchant_id,
        "order_id": order_id,
        "payment_id": payment_id,
        "payment_status": payment_status,
        "payment_amount": money(amount),
        "payment_currency": "INR",
        "payment_timestamp": payment_timestamp.isoformat(),
        "settlement_id": settlement_id,
        "settlement_amount": money(settlement),
        "settlement_currency": "INR",
        "settlement_timestamp": (
            settlement_timestamp.isoformat()
            if settlement_id
            else ""
        ),
        "fee_id": fee_id if fee else "",
        "fee_amount": money(fee),
        "fee_type": "PROCESSING_FEE" if fee else "",
        "tax_amount": money(tax),
        "refund_id": refund_id if refund else "",
        "refund_amount": money(refund),
        "refund_status": refund_status,
        "adjustment_id": adjustment_id,
        "adjustment_amount": "0.00",
        "scenario_type": scenario,
        "ground_truth": scenario,
    }

    # Keep the mathematically expected value available for validation.
    row["_expected_amount"] = money(expected_amount)

    return row


def generate_dataset() -> None:
    rng = random.Random(SEED)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    records = []

    for index in range(1, TRANSACTION_COUNT + 1):
        scenario = rng.choices(
            SCENARIOS,
            weights=SCENARIO_WEIGHTS,
            k=1,
        )[0]

        records.append(
            build_record(
                rng,
                index,
                scenario,
            )
        )

    output_file = OUTPUT_DIR / "transactions.csv"

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
        )

        writer.writeheader()

        for record in records:
            clean_record = {
                key: record[key]
                for key in FIELDNAMES
            }

            writer.writerow(clean_record)

    print(f"Generated {len(records)} transaction cases.")
    print(f"Output: {output_file}")

    print("\nScenario distribution:")

    counts = {}

    for record in records:
        scenario = record["scenario_type"]
        counts[scenario] = counts.get(scenario, 0) + 1

    for scenario in SCENARIOS:
        print(
            f"{scenario:30} "
            f"{counts.get(scenario, 0):3}"
        )


if __name__ == "__main__":
    generate_dataset()