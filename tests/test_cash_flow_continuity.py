"""Tests for rolling quarterly cash-flow continuity."""

import pytest

from tools.financial_statements.cash_flow_continuity import (
    continuous_cash_flow_quarters,
)


def quarter(start, end, value):
    return {
        "start": start,
        "end": end,
        "val": value,
    }


def sample():
    return [
        quarter("2025-09-28", "2025-12-27", 100),
        quarter("2025-12-28", "2026-03-28", 150),
        quarter("2026-03-29", "2026-06-27", 200),
        quarter("2025-06-29", "2025-09-27", 175),
    ]


def test_returns_latest_quarter_first():
    result = continuous_cash_flow_quarters(sample())

    assert result[0]["end"] == "2026-06-27"


def test_four_consecutive_quarters():
    result = continuous_cash_flow_quarters(sample())

    assert len(result) == 4


def test_quarterly_values_preserved():
    result = continuous_cash_flow_quarters(sample())

    assert [item["val"] for item in result] == [200, 150, 100, 175]


def test_stops_at_missing_quarter():
    records = [
        item for item in sample()
        if item["end"] != "2026-03-28"
    ]

    result = continuous_cash_flow_quarters(records)

    assert len(result) == 1


def test_respects_limit():
    result = continuous_cash_flow_quarters(sample(), limit=2)

    assert len(result) == 2


def test_limit_one():
    result = continuous_cash_flow_quarters(sample(), limit=1)

    assert len(result) == 1
    assert result[0]["end"] == "2026-06-27"


def test_empty_observations():
    assert continuous_cash_flow_quarters([]) == []


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_invalid_limit(limit):
    with pytest.raises(ValueError):
        continuous_cash_flow_quarters(sample(), limit=limit)


def test_duplicate_reporting_date_does_not_extend_series():
    records = sample() + [
        quarter("2026-03-29", "2026-06-27", 999)
    ]

    result = continuous_cash_flow_quarters(records)

    assert len(result) == 1
