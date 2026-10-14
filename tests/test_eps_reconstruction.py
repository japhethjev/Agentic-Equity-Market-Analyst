"""Tests for quarterly EPS reconstruction."""

from decimal import Decimal

import pytest

from tools.financial_statements.eps_reconstruction import (
    reconstruct_quarterly_eps,
)


def test_apple_fy2025_basic_eps():
    result = reconstruct_quarterly_eps(
        27466000000,
        14815306000,
    )

    assert result.quantize(Decimal("0.01")) == Decimal("1.85")


def test_apple_fy2025_diluted_eps():
    result = reconstruct_quarterly_eps(
        27466000000,
        14863610000,
    )

    assert result.quantize(Decimal("0.01")) == Decimal("1.85")


def test_eps_preserves_decimal_precision():
    result = reconstruct_quarterly_eps(10, 4)

    assert result == Decimal("2.5")


def test_negative_net_income_is_supported():
    result = reconstruct_quarterly_eps(-100, 50)

    assert result == Decimal("-2")


@pytest.mark.parametrize(
    "shares",
    [0, -1, -1000],
)
def test_nonpositive_shares_rejected(shares):
    with pytest.raises(ValueError):
        reconstruct_quarterly_eps(100, shares)


@pytest.mark.parametrize(
    "income,shares",
    [
        ("invalid", 100),
        (100, "invalid"),
        ("NaN", 100),
        (100, "Infinity"),
    ],
)
def test_invalid_inputs_rejected(income, shares):
    with pytest.raises(ValueError):
        reconstruct_quarterly_eps(income, shares)
