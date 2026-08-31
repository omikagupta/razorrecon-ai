from decimal import Decimal

from app.services.reconciliation.rules import amounts_match


def test_amounts_match_equal_decimal_values():
    assert amounts_match(
        Decimal("100.00"),
        Decimal("100.00"),
    ) is True


def test_amounts_match_different_values():
    assert amounts_match(
        Decimal("100.00"),
        Decimal("99.99"),
    ) is False


def test_amounts_match_one_cent_difference():
    assert amounts_match(
        Decimal("100.00"),
        Decimal("100.01"),
    ) is False


def test_amounts_match_zero_values():
    assert amounts_match(
        Decimal("0.00"),
        Decimal("0.00"),
    ) is True


def test_amounts_match_none_payment():
    assert amounts_match(
        None,
        Decimal("100.00"),
    ) is False


def test_amounts_match_none_settlement():
    assert amounts_match(
        Decimal("100.00"),
        None,
    ) is False


def test_amounts_match_both_none():
    assert amounts_match(
        None,
        None,
    ) is False


def test_amounts_match_string_decimal_values():
    assert amounts_match(
        "100.50",
        "100.50",
    ) is True