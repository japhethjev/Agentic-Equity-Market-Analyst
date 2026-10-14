"""Tests for cumulative-to-quarterly cash-flow reconstruction."""

from decimal import Decimal

from tools.financial_statements.cash_flow_reconstruction import (
    reconstruct_quarterly_cash_flows,
)


def record(start, end, value, filed="2026-10-30", accn="filing-1"):
    return {
        "start": start,
        "end": end,
        "val": value,
        "filed": filed,
        "accn": accn,
        "form": "10-K" if end == "2026-09-26" else "10-Q",
    }


def sample():
    start = "2025-09-28"

    return [
        record(start, "2025-12-27", 100),
        record(start, "2026-03-28", 250),
        record(start, "2026-06-27", 400),
        record(start, "2026-09-26", 600),
    ]


def test_reconstruct_four_quarters():
    result = reconstruct_quarterly_cash_flows(sample())

    assert len(result) == 4

    values = {item["quarter"]: item["val"] for item in result}

    assert values == {
        1: Decimal("100"),
        2: Decimal("150"),
        3: Decimal("150"),
        4: Decimal("200"),
    }


def test_reconciliation_to_full_year():
    result = reconstruct_quarterly_cash_flows(sample())

    assert sum(item["val"] for item in result) == Decimal("600")


def test_latest_quarter_first():
    result = reconstruct_quarterly_cash_flows(sample())

    assert result[0]["quarter"] == 4
    assert result[0]["end"] == "2026-09-26"


def test_missing_q2_prevents_q3_reconstruction():
    records = [sample()[0], sample()[2], sample()[3]]

    result = reconstruct_quarterly_cash_flows(records)

    assert len(result) == 1
    assert result[0]["quarter"] == 1


def test_latest_amended_filing_preferred():
    records = sample()

    amended = record(
        "2025-09-28",
        "2026-03-28",
        260,
        filed="2026-11-15",
        accn="amended-filing",
    )
    amended["form"] = "10-Q/A"

    result = reconstruct_quarterly_cash_flows(records + [amended])

    q2 = next(item for item in result if item["quarter"] == 2)

    assert q2["val"] == Decimal("160")
    assert "amended-filing" in q2["source_accessions"]


def test_missing_fiscal_year_start_not_combined():
    records = [
        record("2025-09-28", "2025-12-27", 100),
        record("2024-09-29", "2025-03-29", 250),
    ]

    result = reconstruct_quarterly_cash_flows(records)

    assert all(item["quarter"] == 1 for item in result)


def test_preserves_source_provenance():
    result = reconstruct_quarterly_cash_flows(sample())

    q2 = next(item for item in result if item["quarter"] == 2)

    assert len(q2["source_accessions"]) == 2
    assert q2["calculation"] == "CUMULATIVE_DIFFERENCE"


def test_invalid_observations_ignored():
    records = sample() + [
        record("2025-09-28", "2026-03-28", "invalid"),
    ]

    result = reconstruct_quarterly_cash_flows(records)

    assert len(result) == 4
