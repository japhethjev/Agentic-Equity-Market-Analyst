"""Regression tests for liquidity validation controls."""

from decimal import Decimal

import pytest

from tools.financial_analysis.liquidity_validation import (
    validate_liquidity_history,
)


def valid_liquidity():
    """Construct one valid quarterly liquidity observation."""
    return {
        "annual": [],
        "quarterly": [{
            "period_end": "2026-06-27",
            "period_type": "quarterly",
            "metrics": {
                "current_ratio": {
                    "status": "available",
                    "value": Decimal("1.20"),
                },
                "quick_ratio": {
                    "status": "available",
                    "value": Decimal("1.10"),
                },
                "cash_ratio": {
                    "status": "available",
                    "value": Decimal("0.40"),
                },
                "operating_cash_flow_ratio": {
                    "status": "available",
                    "value": Decimal("0.95"),
                    "denominator_method": "average_balance",
                    "annualized": True,
                },
            },
        }],
        "ttm": [],
    }


def test_valid_liquidity_passes():
    result = validate_liquidity_history(valid_liquidity())

    assert result["status"] == "validated"
    assert result["checks"] == 4
    assert result["errors"] == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("value", Decimal("NaN")),
        ("denominator_method", "unsupported_method"),
        ("annualized", False),
    ],
)
def test_invalid_ocf_ratio_fails(field, value):
    liquidity = valid_liquidity()

    liquidity["quarterly"][0]["metrics"][
        "operating_cash_flow_ratio"
    ][field] = value

    result = validate_liquidity_history(liquidity)

    assert result["status"] == "failed"
    assert result["errors"]
