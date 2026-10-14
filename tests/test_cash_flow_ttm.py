"""Tests for trailing-twelve-month cash-flow calculations."""

from decimal import Decimal

from tools.financial_statements.cash_flow_ttm import (
    calculate_cash_flow_ttm,
)


def quarter(start, end, value):
    return {"start": start, "end": end, "val": value}


def sample_quarters():
    return [
        quarter("2026-03-29", "2026-06-27", 40),
        quarter("2025-12-28", "2026-03-28", 30),
        quarter("2025-09-28", "2025-12-27", 20),
        quarter("2025-06-29", "2025-09-27", 10),
    ]


def dataset(records):
    return {
        "operating_cash_flow": {
            "quarterly_observations": records,
        }
    }


def test_valid_ttm():
    result = calculate_cash_flow_ttm(
        dataset(sample_quarters()), "2026-06-27"
    )

    assert result["operating_cash_flow"]["status"] == "available"
    assert result["operating_cash_flow"]["ttm"] == Decimal("100")


def test_missing_quarter():
    records = sample_quarters()
    records.pop(1)

    result = calculate_cash_flow_ttm(
        dataset(records), "2026-06-27"
    )

    assert result["operating_cash_flow"]["status"] == "insufficient_data"


def test_wrong_reporting_date():
    result = calculate_cash_flow_ttm(
        dataset(sample_quarters()), "2026-09-26"
    )

    assert result["operating_cash_flow"]["status"] == "insufficient_data"


def test_invalid_financial_value():
    records = sample_quarters()
    records[1]["val"] = "invalid"

    result = calculate_cash_flow_ttm(
        dataset(records), "2026-06-27"
    )

    assert result["operating_cash_flow"]["status"] == "invalid_data"


def test_nonfinite_value():
    records = sample_quarters()
    records[0]["val"] = "NaN"

    result = calculate_cash_flow_ttm(
        dataset(records), "2026-06-27"
    )

    assert result["operating_cash_flow"]["status"] == "invalid_data"


def test_only_three_quarters():
    result = calculate_cash_flow_ttm(
        dataset(sample_quarters()[:3]), "2026-06-27"
    )

    assert result["operating_cash_flow"]["status"] == "insufficient_data"


def test_historical_quarters_not_current():
    records = [
        quarter("2017-10-01", "2017-12-30", 10),
        quarter("2017-07-02", "2017-09-30", 10),
        quarter("2017-04-02", "2017-07-01", 10),
        quarter("2017-01-01", "2017-04-01", 10),
    ]

    result = calculate_cash_flow_ttm(
        dataset(records), "2026-06-27"
    )

    assert result["operating_cash_flow"]["status"] == "insufficient_data"


def test_quarter_provenance_dates():
    result = calculate_cash_flow_ttm(
        dataset(sample_quarters()), "2026-06-27"
    )

    assert result["operating_cash_flow"]["quarters_used"] == [
        "2026-06-27",
        "2026-03-28",
        "2025-12-27",
        "2025-09-27",
    ]
