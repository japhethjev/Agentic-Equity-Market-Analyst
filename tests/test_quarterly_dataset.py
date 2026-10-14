"""Tests for rolling quarterly financial datasets."""

import pytest

from tools.financial_statements.quarterly_dataset import (
    build_rolling_quarterly_dataset,
)


def record(start, end, value, form="10-Q"):
    return {
        "start": start,
        "end": end,
        "val": value,
        "form": form,
        "filed": "2026-08-01",
        "accn": f"filing-{end}",
    }


def sample_records():
    return [
        record("2025-01-01", "2025-03-31", 100),
        record("2025-04-01", "2025-06-30", 120),
        record("2025-07-01", "2025-09-30", 140),
        record("2025-10-01", "2025-12-31", 160),
    ]


def test_four_consecutive_quarters():
    result = build_rolling_quarterly_dataset(
        sample_records(),
        quarters=4,
    )

    assert len(result) == 4
    assert result[0]["val"] == 160
    assert result[-1]["val"] == 100


def test_latest_quarter_first():
    result = build_rolling_quarterly_dataset(
        sample_records(),
    )

    assert result[0]["end"] == "2025-12-31"


def test_stop_at_missing_quarter():
    records = [
        record("2025-01-01", "2025-03-31", 100),
        record("2025-07-01", "2025-09-30", 140),
    ]

    result = build_rolling_quarterly_dataset(records)

    assert len(result) == 1
    assert result[0]["val"] == 140


def test_empty_observations():
    assert build_rolling_quarterly_dataset([]) == []


def test_invalid_quarter_count():
    with pytest.raises(ValueError, match="quarters"):
        build_rolling_quarterly_dataset(
            sample_records(),
            quarters=0,
        )


def test_boolean_quarter_count_rejected():
    with pytest.raises(ValueError, match="quarters"):
        build_rolling_quarterly_dataset(
            sample_records(),
            quarters=True,
        )
