"""Tests for cash-flow reporting-date alignment."""

from tools.financial_statements.cash_flow_alignment import (
    align_cash_flow_metrics,
)


def metric(concept, dates):
    return {
        "concept": concept,
        "quarterly_observations": [
            {"end": end, "val": value}
            for end, value in dates
        ],
    }


def sample():
    return {
        "operating_cash_flow": metric(
            "OperatingCashFlow",
            [
                ("2026-06-27", 100),
                ("2026-03-28", 80),
            ],
        ),
        "capital_expenditure": metric(
            "CapitalExpenditure",
            [
                ("2026-06-27", 20),
                ("2026-03-28", 15),
            ],
        ),
        "common_stock_dividends": metric(
            "CommonStockDividends",
            [
                ("2017-12-30", 10),
            ],
        ),
    }


def test_latest_reporting_date():
    result = align_cash_flow_metrics(sample())

    assert result["reporting_date"] == "2026-06-27"


def test_current_metrics_aligned():
    result = align_cash_flow_metrics(sample())

    assert result["metrics"]["operating_cash_flow"]["status"] == "aligned"
    assert result["metrics"]["capital_expenditure"]["status"] == "aligned"


def test_historical_metric_unavailable():
    result = align_cash_flow_metrics(sample())

    assert (
        result["metrics"]["common_stock_dividends"]["status"]
        == "unavailable_for_period"
    )
    assert result["metrics"]["common_stock_dividends"]["observation"] is None


def test_aligned_values_preserved():
    result = align_cash_flow_metrics(sample())

    assert result["metrics"]["operating_cash_flow"]["observation"]["val"] == 100


def test_empty_dataset():
    result = align_cash_flow_metrics({})

    assert result["reporting_date"] is None
    assert result["metrics"] == {}


def test_all_metrics_without_observations():
    data = {
        "operating_cash_flow": metric("OperatingCashFlow", []),
    }

    result = align_cash_flow_metrics(data)

    assert result["reporting_date"] is None
    assert result["metrics"] == {}


def test_metric_missing_latest_quarter():
    data = sample()
    data["capital_expenditure"] = metric(
        "CapitalExpenditure",
        [("2026-03-28", 15)],
    )

    result = align_cash_flow_metrics(data)

    assert (
        result["metrics"]["capital_expenditure"]["status"]
        == "unavailable_for_period"
    )
