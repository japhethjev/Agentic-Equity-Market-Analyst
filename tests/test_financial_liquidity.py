from decimal import Decimal

from tools.financial_analysis.liquidity import calculate_liquidity_ratios


def make_balance_sheet(
    assets=200,
    inventory=40,
    liabilities=100,
    cash=50,
):
    return {
        "period_end": "2026-06-30",
        "metrics": {
            "current_assets": {"value": assets},
            "inventory": {"value": inventory},
            "current_liabilities": {"value": liabilities},
            "cash_and_equivalents": {"value": cash},
        },
    }


def test_liquidity_ratios():
    result = calculate_liquidity_ratios(make_balance_sheet())

    assert result["current_ratio"]["value"] == Decimal("2")
    assert result["quick_ratio"]["value"] == Decimal("1.6")
    assert result["cash_ratio"]["value"] == Decimal("0.5")
    assert all(r["status"] == "available" for r in result.values())


def test_missing_inventory():
    sheet = make_balance_sheet()
    del sheet["metrics"]["inventory"]

    result = calculate_liquidity_ratios(sheet)

    assert result["quick_ratio"]["status"] == "insufficient_data"
    assert result["current_ratio"]["status"] == "available"
    assert result["cash_ratio"]["status"] == "available"


def test_zero_current_liabilities():
    result = calculate_liquidity_ratios(
        make_balance_sheet(liabilities=0)
    )

    assert all(r["value"] is None for r in result.values())
    assert all(r["status"] == "not_meaningful" for r in result.values())


def test_negative_current_liabilities():
    result = calculate_liquidity_ratios(
        make_balance_sheet(liabilities=-100)
    )

    assert all(r["status"] == "not_meaningful" for r in result.values())


def test_missing_current_liabilities():
    sheet = make_balance_sheet()
    del sheet["metrics"]["current_liabilities"]

    result = calculate_liquidity_ratios(sheet)

    assert all(
        r["status"] == "insufficient_data"
        for r in result.values()
    )


def test_negative_quick_ratio_numerator():
    result = calculate_liquidity_ratios(
        make_balance_sheet(assets=20, inventory=40)
    )

    assert result["quick_ratio"]["status"] == "not_meaningful"
    assert result["quick_ratio"]["value"] is None


def test_invalid_numeric_input():
    result = calculate_liquidity_ratios(
        make_balance_sheet(assets="invalid")
    )

    assert result["current_ratio"]["status"] == "insufficient_data"
    assert result["quick_ratio"]["status"] == "insufficient_data"
    assert result["cash_ratio"]["status"] == "available"


def test_ratio_provenance():
    result = calculate_liquidity_ratios(make_balance_sheet())

    for ratio in result.values():
        assert ratio["period_end"] == "2026-06-30"
        assert ratio["unit"] == "times"
        assert ratio["denominator_method"] == "closing_balance"
        assert ratio["source_metrics"]
