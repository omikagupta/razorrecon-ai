
from decimal import Decimal

from app.services.reconciliation.rules import amounts_match


def test_amounts_match_exact_values():
    assert amounts_match(
        Decimal("100.00"),
        Decimal("100.00"),
    )


def test_amounts_match_different_values():
    assert not amounts_match(
        Decimal("100.00"),
        Decimal("99.99"),
    )


def test_amounts_match_zero_values():
    assert amounts_match(
        Decimal("0.00"),
        Decimal("0.00"),
    )


def test_amounts_match_large_values():
    assert amounts_match(
        Decimal("999999.99"),
        Decimal("999999.99"),
    )

