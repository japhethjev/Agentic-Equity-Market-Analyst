"""Regression tests for financial profitability calculations."""

from decimal import Decimal

from tools.financial_analysis.profitability import (
    calculate_profitability_ratios,
)


def test_profitability_margins():
    statement = {
        "period_end": "2026-06-30",
        "metrics": {
            "revenue": {"value": Decimal("100000000")},
            "gross_profit": {"value": Decimal("40000000")},
            "operating_income": {"value": Decimal("25000000")},
            "net_income": {"value": Decimal("18000000")},
        },
    }

    result = calculate_profitability_ratios(statement)

    assert result["gross_profit_margin"]["value"] == Decimal("40")
    assert result["operating_profit_margin"]["value"] == Decimal("25")
    assert result["net_profit_margin"]["value"] == Decimal("18")
    assert all(item["status"] == "available" for item in result.values())
    assert all(item["period_end"] == "2026-06-30" for item in result.values())


def test_missing_profitability_metric():
    statement = {
        "period_end": "2026-06-30",
        "metrics": {
            "revenue": {"value": Decimal("100000000")},
            "net_income": {"value": Decimal("15000000")},
        },
    }

    result = calculate_profitability_ratios(statement)

    assert result["net_profit_margin"]["value"] == Decimal("15")
    assert result["gross_profit_margin"]["status"] == "insufficient_data"
    assert result["operating_profit_margin"]["value"] is None


def test_zero_revenue():
    statement = {
        "period_end": "2026-06-30",
        "metrics": {
            "revenue": {"value": Decimal("0")},
            "gross_profit": {"value": Decimal("100")},
            "operating_income": {"value": Decimal("80")},
            "net_income": {"value": Decimal("50")},
        },
    }

    result = calculate_profitability_ratios(statement)

    assert all(item["status"] == "insufficient_data" for item in result.values())
    assert all(item["value"] is None for item in result.values())


def test_return_ratios_all_periods():
    from tools.financial_analysis.profitability import (
        calculate_period_return_ratios,
    )

    balance_sheets = [
        {
            "period_end": date,
            "metrics": {
                "total_assets": {"value": Decimal("200")},
                "shareholders_equity": {"value": Decimal("100")},
            },
        }
        for date in (
            "2025-06-30",
            "2026-03-31",
            "2026-06-30",
        )
    ]

    cases = [
        (
            "annual",
            {"period_start": "2025-07-01", "period_end": "2026-06-30"},
            Decimal("1"),
        ),
        (
            "quarterly",
            {"period_start": "2026-04-01", "period_end": "2026-06-30"},
            Decimal("365.25") / Decimal("91"),
        ),
        (
            "ttm",
            {"period_start": "2025-07-01", "period_end": "2026-06-30"},
            Decimal("1"),
        ),
    ]

    for period_type, dates, factor in cases:
        statement = {
            **dates,
            "metrics": {"net_income": {"value": Decimal("20")}},
        }

        result = calculate_period_return_ratios(
            statement, balance_sheets, period_type
        )

        assert result["return_on_assets"]["status"] == "available"
        assert result["return_on_equity"]["status"] == "available"
        assert result["return_on_assets"]["value"] == Decimal("10") * factor
        assert result["return_on_equity"]["value"] == Decimal("20") * factor


def test_return_ratios_missing_opening_balance():
    from tools.financial_analysis.profitability import (
        calculate_period_return_ratios,
    )

    statement = {
        "period_start": "2025-07-01",
        "period_end": "2026-06-30",
        "metrics": {"net_income": {"value": Decimal("20")}},
    }
    balances = [{
        "period_end": "2026-06-30",
        "metrics": {
            "total_assets": {"value": Decimal("200")},
            "shareholders_equity": {"value": Decimal("100")},
        },
    }]

    result = calculate_period_return_ratios(statement, balances, "ttm")

    assert result["return_on_assets"]["status"] == "available"
    assert result["return_on_equity"]["status"] == "available"

    assert result["return_on_assets"]["value"] == Decimal("10")
    assert result["return_on_equity"]["value"] == Decimal("20")

    assert all(
        r["denominator_method"] == "closing_balance"
        for r in result.values()
    )


def test_return_on_equity_negative_average_equity():
    from tools.financial_analysis.profitability import (
        calculate_period_return_ratios,
    )

    statement = {
        "period_start": "2025-07-01",
        "period_end": "2026-06-30",
        "metrics": {"net_income": {"value": Decimal("20")}},
    }
    balances = [
        {
            "period_end": date,
            "metrics": {
                "total_assets": {"value": Decimal("200")},
                "shareholders_equity": {"value": Decimal("-50")},
            },
        }
        for date in ("2025-06-30", "2026-06-30")
    ]

    result = calculate_period_return_ratios(statement, balances, "ttm")

    assert result["return_on_assets"]["value"] == Decimal("10")
    assert result["return_on_equity"]["status"] == "not_meaningful"
    assert result["return_on_equity"]["value"] is None


def test_return_ratios_53_week_fiscal_calendar():
    """Use actual fiscal boundaries, not a calendar-year approximation."""
    from tools.financial_analysis.profitability import (
        calculate_period_return_ratios,
    )

    statement = {
        "period_end": "2024-09-28",
        "metrics": {
            "net_income": {
                "value": Decimal("30"),
                "period_start": "2023-10-01",
            },
        },
    }

    balances = [
        {
            "period_end": "2023-09-30",
            "metrics": {
                "total_assets": {"value": Decimal("200")},
                "shareholders_equity": {"value": Decimal("100")},
            },
        },
        {
            "period_end": "2024-09-28",
            "metrics": {
                "total_assets": {"value": Decimal("400")},
                "shareholders_equity": {"value": Decimal("200")},
            },
        },
    ]

    result = calculate_period_return_ratios(
        statement, balances, "annual"
    )

    assert result["return_on_assets"]["value"] == Decimal("10")
    assert result["return_on_equity"]["value"] == Decimal("20")
    assert result["return_on_assets"]["opening_balance_date"] == "2023-09-30"
    assert result["return_on_equity"]["closing_balance_date"] == "2024-09-28"
