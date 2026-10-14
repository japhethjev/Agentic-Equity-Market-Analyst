"""Tests for fourth-quarter financial reconstruction."""

from tools.financial_statements.quarter_reconstruction import (
    reconstruct_fourth_quarters,
)


def annual_record(value=1000):
    return {
        "start": "2024-09-29",
        "end": "2025-09-27",
        "val": value,
        "form": "10-K",
        "filed": "2025-10-31",
        "accn": "annual-2025",
    }


def nine_month_record(value=750):
    return {
        "start": "2024-09-29",
        "end": "2025-06-28",
        "val": value,
        "form": "10-Q",
        "filed": "2025-08-01",
        "accn": "nine-month-2025",
    }


def test_reconstruct_q4():
    result = reconstruct_fourth_quarters([
        annual_record(),
        nine_month_record(),
    ])

    assert len(result) == 1
    assert result[0]["val"] == 250
    assert result[0]["derived"] is True


def test_q4_reporting_dates():
    result = reconstruct_fourth_quarters([
        annual_record(),
        nine_month_record(),
    ])

    assert result[0]["start"] == "2025-06-29"
    assert result[0]["end"] == "2025-09-27"


def test_preserve_source_provenance():
    result = reconstruct_fourth_quarters([
        annual_record(),
        nine_month_record(),
    ])

    assert result[0]["fy_accn"] == "annual-2025"
    assert result[0]["nine_month_accn"] == "nine-month-2025"
    assert result[0]["calculation"] == "FY_MINUS_9M"


def test_missing_nine_month_data():
    result = reconstruct_fourth_quarters([
        annual_record(),
    ])

    assert result == []


def test_reject_mismatched_fiscal_year():
    nine_month = nine_month_record()
    nine_month["start"] = "2023-10-01"

    result = reconstruct_fourth_quarters([
        annual_record(),
        nine_month,
    ])

    assert result == []


def test_prefer_latest_nine_month_filing():
    original = nine_month_record(value=750)

    amended = nine_month_record(value=740)
    amended["filed"] = "2025-08-15"
    amended["form"] = "10-Q/A"
    amended["accn"] = "nine-month-amended"

    result = reconstruct_fourth_quarters([
        annual_record(),
        original,
        amended,
    ])

    assert len(result) == 1
    assert result[0]["val"] == 260
    assert result[0]["nine_month_accn"] == "nine-month-amended"
