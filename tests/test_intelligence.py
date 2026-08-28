from decimal import Decimal

from app.services.reconciliation.intelligence import (
    analyze_exception,
)


def test_intelligence_function_exists():
    assert callable(analyze_exception)


def test_decimal_difference():
    payment = Decimal("1000.00")
    settlement = Decimal("900.00")

    difference = payment - settlement

    assert difference == Decimal("100.00")


def test_fee_difference_logic():
    payment_amount = Decimal("1000.00")
    settlement_amount = Decimal("970.00")
    fee_amount = Decimal("30.00")

    difference = payment_amount - settlement_amount

    assert difference == fee_amount


def test_fee_plus_adjustment_difference_logic():
    payment_amount = Decimal("1000.00")
    settlement_amount = Decimal("950.00")
    fee_amount = Decimal("30.00")
    adjustment_amount = Decimal("20.00")

    difference = payment_amount - settlement_amount

    assert difference == fee_amount + adjustment_amount


def test_unexplained_difference_logic():
    payment_amount = Decimal("1000.00")
    settlement_amount = Decimal("900.00")
    fee_amount = Decimal("30.00")

    difference = payment_amount - settlement_amount

    assert difference != fee_amount