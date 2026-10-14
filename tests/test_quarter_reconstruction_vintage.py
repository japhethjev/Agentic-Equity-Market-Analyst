"""Regression tests for Q4 filing-vintage selection."""

from tools.financial_statements.quarter_reconstruction import (
    reconstruct_fourth_quarters,
)


def observation(start, end, value, form, filed, accession):
    return {
        "start": start,
        "end": end,
        "val": value,
        "form": form,
        "filed": filed,
        "accn": accession,
    }


def test_later_comparative_filing_is_excluded():
    observations = [
        observation(
            "2024-09-29", "2025-09-27",
            400, "10-K", "2025-10-31", "annual-001",
        ),
        observation(
            "2024-09-29", "2025-06-28",
            300, "10-Q", "2025-08-01", "original-q3",
        ),
        observation(
            "2024-09-29", "2025-06-28",
            310, "10-Q", "2026-07-31", "later-comparative",
        ),
    ]

    result = reconstruct_fourth_quarters(observations)

    assert len(result) == 1
    assert result[0]["val"] == 100
    assert result[0]["nine_month_accn"] == "original-q3"
    assert result[0]["fy_accn"] == "annual-001"


def test_no_eligible_nine_month_filing():
    observations = [
        observation(
            "2024-09-29", "2025-09-27",
            400, "10-K", "2025-10-31", "annual-001",
        ),
        observation(
            "2024-09-29", "2025-06-28",
            300, "10-Q", "2026-07-31", "later-only",
        ),
    ]

    assert reconstruct_fourth_quarters(observations) == []


def test_latest_eligible_filing_is_selected():
    observations = [
        observation(
            "2024-09-29", "2025-09-27",
            400, "10-K", "2025-10-31", "annual-001",
        ),
        observation(
            "2024-09-29", "2025-06-28",
            290, "10-Q", "2025-08-01", "original-q3",
        ),
        observation(
            "2024-09-29", "2025-06-28",
            300, "10-Q/A", "2025-09-01", "amended-q3",
        ),
    ]

    result = reconstruct_fourth_quarters(observations)

    assert len(result) == 1
    assert result[0]["val"] == 100
    assert result[0]["nine_month_accn"] == "amended-q3"
