from datetime import datetime
from decimal import Decimal

import pytest

from app.services.ingestion.csv_ingestion import load_transactions


HEADERS = [
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


def write_csv(tmp_path, content):
    path = tmp_path / "transactions.csv"
    path.write_text(content, encoding="utf-8")
    return path


def valid_row():
    return (
        "txn_001,merchant_001,order_001,pay_001,CAPTURED,"
        "1000.00,INR,2026-01-01T10:00:00,"
        "set_001,1000.00,INR,2026-01-02T10:00:00,"
        "fee_001,20.00,PROCESSING,3.60,"
        "refund_001,100.00,COMPLETED,"
        "adj_001,0.00,MATCHED,MATCHED"
    )


def test_load_valid_transaction(tmp_path):
    content = ",".join(HEADERS) + "\n" + valid_row() + "\n"

    path = write_csv(tmp_path, content)

    transactions = load_transactions(path)

    assert len(transactions) == 1

    transaction = transactions[0]

    assert transaction.transaction_id == "txn_001"
    assert transaction.merchant_id == "merchant_001"
    assert transaction.order_id == "order_001"
    assert transaction.payment_id == "pay_001"
    assert transaction.payment_status == "CAPTURED"
    assert transaction.payment_amount == Decimal("1000.00")
    assert transaction.payment_currency == "INR"
    assert transaction.settlement_id == "set_001"
    assert transaction.settlement_amount == Decimal("1000.00")
    assert transaction.fee_id == "fee_001"
    assert transaction.refund_id == "refund_001"
    assert transaction.adjustment_id == "adj_001"


def test_missing_file_raises_error(tmp_path):
    path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        load_transactions(path)


def test_empty_csv_raises_error(tmp_path):
    path = write_csv(tmp_path, "")

    with pytest.raises(ValueError, match="no header"):
        load_transactions(path)


def test_missing_required_column_raises_error(tmp_path):
    headers = HEADERS[:-1]

    content = ",".join(headers) + "\n"

    path = write_csv(tmp_path, content)

    with pytest.raises(ValueError, match="missing required columns"):
        load_transactions(path)


def test_invalid_decimal_raises_error(tmp_path):
    row = valid_row().replace("1000.00", "INVALID", 1)

    content = ",".join(HEADERS) + "\n" + row + "\n"

    path = write_csv(tmp_path, content)

    with pytest.raises(ValueError, match="Invalid transaction at CSV row 2"):
        load_transactions(path)


def test_invalid_datetime_raises_error(tmp_path):
    row = valid_row().replace(
        "2026-01-01T10:00:00",
        "INVALID_DATE",
        1,
    )

    content = ",".join(HEADERS) + "\n" + row + "\n"

    path = write_csv(tmp_path, content)

    with pytest.raises(ValueError, match="Invalid transaction at CSV row 2"):
        load_transactions(path)


def test_missing_transaction_id_raises_error(tmp_path):
    row = valid_row().replace("txn_001", "", 1)

    content = ",".join(HEADERS) + "\n" + row + "\n"

    path = write_csv(tmp_path, content)

    with pytest.raises(
        ValueError,
        match="Missing transaction_id at CSV row 2",
    ):
        load_transactions(path)


def test_optional_fields_are_converted_to_none(tmp_path):
    row = valid_row().split(",")

    # Map each column name to its position.
    row[HEADERS.index("settlement_id")] = ""
    row[HEADERS.index("settlement_amount")] = ""
    row[HEADERS.index("settlement_currency")] = ""
    row[HEADERS.index("settlement_timestamp")] = ""

    row[HEADERS.index("fee_id")] = ""
    row[HEADERS.index("fee_type")] = ""

    row[HEADERS.index("refund_id")] = ""
    row[HEADERS.index("refund_status")] = ""

    row[HEADERS.index("adjustment_id")] = ""

    content = ",".join(HEADERS) + "\n" + ",".join(row) + "\n"

    path = write_csv(tmp_path, content)

    transactions = load_transactions(path)

    transaction = transactions[0]

    assert transaction.settlement_id is None
    assert transaction.settlement_amount is None
    assert transaction.settlement_currency is None
    assert transaction.settlement_timestamp is None

    assert transaction.fee_id is None
    assert transaction.fee_type is None

    assert transaction.refund_id is None
    assert transaction.refund_status is None

    assert transaction.adjustment_id is None

def test_status_and_currency_are_normalized(tmp_path):
    row = valid_row()
    row = row.replace("CAPTURED", " captured ", 1)
    row = row.replace("INR", " inr ", 1)

    content = ",".join(HEADERS) + "\n" + row + "\n"

    path = write_csv(tmp_path, content)

    transaction = load_transactions(path)[0]

    assert transaction.payment_status == "CAPTURED"
    assert transaction.payment_currency == "INR"


def test_multiple_transactions_are_loaded(tmp_path):
    row1 = valid_row()

    row2 = valid_row().replace(
        "txn_001,merchant_001,order_001,pay_001",
        "txn_002,merchant_002,order_002,pay_002",
    )

    content = (
        ",".join(HEADERS)
        + "\n"
        + row1
        + "\n"
        + row2
        + "\n"
    )

    path = write_csv(tmp_path, content)

    transactions = load_transactions(path)

    assert len(transactions) == 2
    assert transactions[0].transaction_id == "txn_001"
    assert transactions[1].transaction_id == "txn_002"
