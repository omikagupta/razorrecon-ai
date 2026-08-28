import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path


@dataclass
class TransactionRecord:
    transaction_id: str
    merchant_id: str
    order_id: str
    payment_id: str
    payment_status: str
    payment_amount: Decimal
    payment_currency: str
    payment_timestamp: datetime

    settlement_id: str | None
    settlement_amount: Decimal | None
    settlement_currency: str | None
    settlement_timestamp: datetime | None

    fee_id: str | None
    fee_amount: Decimal
    fee_type: str | None

    tax_amount: Decimal

    refund_id: str | None
    refund_amount: Decimal
    refund_status: str | None

    adjustment_id: str | None
    adjustment_amount: Decimal

    scenario_type: str
    ground_truth: str


REQUIRED_COLUMNS = {
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
}


def _optional_string(value: str) -> str | None:
    value = value.strip()
    return value if value else None


def _decimal(value: str) -> Decimal:
    return Decimal(value.strip())


def _optional_decimal(value: str) -> Decimal | None:
    value = value.strip()
    return Decimal(value) if value else None


def _optional_datetime(value: str) -> datetime | None:
    value = value.strip()
    return datetime.fromisoformat(value) if value else None


def load_transactions(csv_path: str | Path) -> list[TransactionRecord]:
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError("CSV file has no header row")

        missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)

        if missing_columns:
            raise ValueError(
                f"CSV is missing required columns: {sorted(missing_columns)}"
            )

        transactions: list[TransactionRecord] = []

        for row_number, row in enumerate(reader, start=2):
            try:
                transaction = TransactionRecord(
                    transaction_id=row["transaction_id"].strip(),
                    merchant_id=row["merchant_id"].strip(),
                    order_id=row["order_id"].strip(),
                    payment_id=row["payment_id"].strip(),
                    payment_status=row["payment_status"].strip().upper(),
                    payment_amount=_decimal(row["payment_amount"]),
                    payment_currency=row["payment_currency"].strip().upper(),
                    payment_timestamp=datetime.fromisoformat(
                        row["payment_timestamp"].strip()
                    ),
                    settlement_id=_optional_string(row["settlement_id"]),
                    settlement_amount=_optional_decimal(row["settlement_amount"]),
                    settlement_currency=(
                        row["settlement_currency"].strip().upper()
                        if row["settlement_currency"].strip()
                        else None
                    ),
                    settlement_timestamp=_optional_datetime(
                        row["settlement_timestamp"]
                    ),
                    fee_id=_optional_string(row["fee_id"]),
                    fee_amount=_decimal(row["fee_amount"]),
                    fee_type=_optional_string(row["fee_type"]),
                    tax_amount=_decimal(row["tax_amount"]),
                    refund_id=_optional_string(row["refund_id"]),
                    refund_amount=_decimal(row["refund_amount"]),
                    refund_status=_optional_string(row["refund_status"]),
                    adjustment_id=_optional_string(row["adjustment_id"]),
                    adjustment_amount=_decimal(row["adjustment_amount"]),
                    scenario_type=row["scenario_type"].strip(),
                    ground_truth=row["ground_truth"].strip(),
                )

            except (KeyError, ValueError, ArithmeticError) as exc:
                raise ValueError(
                    f"Invalid transaction at CSV row {row_number}: {exc}"
                ) from exc

            if not transaction.transaction_id:
                raise ValueError(
                    f"Missing transaction_id at CSV row {row_number}"
                )

            transactions.append(transaction)

    return transactions