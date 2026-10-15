"""Regression tests for the operating cash flow liquidity ratio."""

from decimal import Decimal

from tools.financial_analysis.liquidity_cash_flow import (
    calculate_operating_cash_flow_ratio,
)


def balance(period, liabilities):
    return {
        "period_end": period,
        "metrics": {
            "current_liabilities": {
                "value": Decimal(str(liabilities))
            }
        },
    }


def cash_flow(period, kind, value, start=None):
    return {
        "period_end": period,
        "period_type": kind,
        "metrics": {
            "operating_cash_flow": {
                "value": Decimal(str(value)),
                "period_start": start,
            }
        },
    }


def test_annual_average_liabilities():
    cf = cash_flow("2025-12-31", "annual", 120, "2025-01-01")
    sheets = [
        balance("2024-12-31", 100),
        balance("2025-12-31", 140),
    ]

    result = calculate_operating_cash_flow_ratio(cf, sheets)

    assert result["value"] == Decimal("1")
    assert result["denominator_method"] == "average_balance"
    assert result["annualized"] is False


def test_quarterly_cash_flow_is_annualized():
    cf = cash_flow("2026-03-31", "quarterly", 30, "2026-01-01")
    sheets = [
        balance("2025-12-31", 100),
        balance("2026-03-31", 140),
    ]

    result = calculate_operating_cash_flow_ratio(cf, sheets)

    assert result["value"] == Decimal("1")
    assert result["annualized"] is True


def test_ttm_uses_actual_oldest_quarter_start():
    oldest = cash_flow(
        "2025-09-27", "quarterly", 20, "2025-06-29"
    )

    cf = {
        "period_end": "2026-06-27",
        "period_type": "ttm",
        "metrics": {
            "operating_cash_flow": {
                "ttm": Decimal("146724000000"),
                "status": "available",
                "quarters_used": [
                    "2026-06-27",
                    "2026-03-28",
                    "2025-12-27",
                    "2025-09-27",
                ],
            }
        },
        "underlying_quarters": [oldest],
    }

    sheets = [
        balance("2025-06-28", 141120000000),
        balance("2026-06-27", 149326000000),
    ]

    result = calculate_operating_cash_flow_ratio(cf, sheets)

    expected = Decimal("146724000000") / Decimal("145223000000")

    assert result["value"] == expected
    assert result["denominator_method"] == "average_balance"
    assert result["annualized"] is False


def test_missing_opening_balance_falls_back_to_closing():
    cf = cash_flow("2025-12-31", "annual", 100, "2025-01-01")

    result = calculate_operating_cash_flow_ratio(
        cf, [balance("2025-12-31", 200)]
    )

    assert result["value"] == Decimal("0.5")
    assert result["denominator_method"] == "closing_balance"


def test_zero_closing_liabilities_not_meaningful():
    cf = cash_flow("2025-12-31", "annual", 100, "2025-01-01")

    result = calculate_operating_cash_flow_ratio(
        cf, [balance("2025-12-31", 0)]
    )

    assert result["value"] is None
    assert result["status"] == "not_meaningful"


def test_missing_operating_cash_flow():
    cf = cash_flow("2025-12-31", "annual", 100, "2025-01-01")
    cf["metrics"]["operating_cash_flow"]["value"] = None

    result = calculate_operating_cash_flow_ratio(
        cf, [balance("2025-12-31", 200)]
    )

    assert result["value"] is None
    assert result["status"] == "insufficient_data"
