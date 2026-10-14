"""Regression tests for Q4 share reconstruction."""

from decimal import Decimal

from tools.financial_statements.quarterly_share_dataset import (
    reconstruct_q4_share_observations,
)


def observation(start, end, value, filed, accn, form):
    return {
        "start": start,
        "end": end,
        "val": value,
        "filed": filed,
        "accn": accn,
        "form": form,
    }


def test_reconstruct_q4_shares_from_original_filings():
    records = [
        observation(
            "2023-10-01", "2024-09-28",
            15200000000, "2024-11-01",
            "annual-2024", "10-K",
        ),
        observation(
            "2023-10-01", "2024-06-29",
            15401047000, "2024-08-02",
            "q3-2024", "10-Q",
        ),
        observation(
            "2023-10-01", "2024-06-29",
            15401047000, "2025-08-01",
            "q3-2025-comparative", "10-Q",
        ),
    ]

    result = reconstruct_q4_share_observations(records)

    assert len(result) == 1
    assert result[0]["nine_month_accn"] == "q3-2024"
    assert result[0]["fy_accn"] == "annual-2024"
    assert result[0]["derived"] is True
    assert isinstance(result[0]["val"], Decimal)


def test_excludes_late_comparative_filing():
    records = [
        observation(
            "2023-10-01", "2024-09-28",
            15200000000, "2024-11-01",
            "annual-2024", "10-K",
        ),
        observation(
            "2023-10-01", "2024-06-29",
            15401047000, "2025-08-01",
            "late-comparative", "10-Q",
        ),
    ]

    assert reconstruct_q4_share_observations(records) == []


def test_requires_matching_fiscal_year_start():
    records = [
        observation(
            "2023-10-01", "2024-09-28",
            15200000000, "2024-11-01",
            "annual-2024", "10-K",
        ),
        observation(
            "2022-10-01", "2024-06-29",
            15401047000, "2024-08-02",
            "wrong-fiscal-start", "10-Q",
        ),
    ]

    assert reconstruct_q4_share_observations(records) == []


def test_rejects_missing_nine_month_filing():
    records = [
        observation(
            "2023-10-01", "2024-09-28",
            15200000000, "2024-11-01",
            "annual-2024", "10-K",
        ),
    ]

    assert reconstruct_q4_share_observations(records) == []


def test_shares_prefer_original_annual_over_later_comparative():
    original = observation(
        "2023-10-01", "2024-09-28",
        15200000000, "2024-11-01",
        "annual-2024", "10-K",
    )

    comparative = observation(
        "2023-10-01", "2024-09-28",
        15300000000, "2025-10-31",
        "annual-2025-comparative", "10-K",
    )

    nine_month = observation(
        "2023-10-01", "2024-06-29",
        15401047000, "2024-08-02",
        "nine-month-2024", "10-Q",
    )

    result = reconstruct_q4_share_observations([
        comparative, nine_month, original
    ])

    assert len(result) == 1
    assert result[0]["fy_accn"] == "annual-2024"
    assert result[0]["nine_month_accn"] == "nine-month-2024"
