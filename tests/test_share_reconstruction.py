"""Tests for quarterly weighted-average share reconstruction."""

from decimal import Decimal

import pytest

from tools.financial_statements.share_reconstruction import (
    reconstruct_q4_weighted_shares,
)


def test_apple_fy2025_basic_shares():
    result = reconstruct_q4_weighted_shares(
        14948500000,
        14992898000,
        "2024-09-29",
        "2025-06-28",
        "2025-09-27",
    )

    assert result == Decimal("14815306000")


def test_apple_fy2025_diluted_shares():
    result = reconstruct_q4_weighted_shares(
        15004697000,
        15051726000,
        "2024-09-29",
        "2025-06-28",
        "2025-09-27",
    )

    assert result == Decimal("14863610000")


def test_equal_share_counts_remain_equal():
    result = reconstruct_q4_weighted_shares(
        1000,
        1000,
        "2024-09-29",
        "2025-06-28",
        "2025-09-27",
    )

    assert result == Decimal("1000")


def test_53_week_fiscal_year():
    result = reconstruct_q4_weighted_shares(
        1000,
        1000,
        "2022-09-25",
        "2023-07-01",
        "2023-09-30",
    )

    assert result == Decimal("1000")


@pytest.mark.parametrize(
    "annual,nine_month",
    [
        (0, 1000),
        (1000, 0),
        (-1000, 1000),
        (1000, -1000),
    ],
)
def test_nonpositive_share_counts_rejected(annual, nine_month):
    with pytest.raises(ValueError):
        reconstruct_q4_weighted_shares(
            annual,
            nine_month,
            "2024-09-29",
            "2025-06-28",
            "2025-09-27",
        )


def test_invalid_reporting_dates_rejected():
    with pytest.raises(ValueError):
        reconstruct_q4_weighted_shares(
            1000,
            1000,
            "2024-09-29",
            "2025-09-27",
            "2025-06-28",
        )


def test_nonpositive_reconstructed_shares_rejected():
    with pytest.raises(ValueError):
        reconstruct_q4_weighted_shares(
            100,
            1000,
            "2024-09-29",
            "2025-06-28",
            "2025-09-27",
        )
