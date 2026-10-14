"""Regression tests for SEC financial statement normalization."""

import pytest

from tools.financial_statements.normalization import (
    normalize_balance_sheet,
    normalize_quarterly_cash_flow,
)


def test_balance_sheet_provenance():
    observation = {
        "end": "2026-06-27",
        "val": 383266000000,
        "accn": "SEC-001",
        "filed": "2026-07-31",
        "form": "10-Q",
    }
    extracted = {
        "total_assets": {
            "concept": "Assets",
            "observations": [observation],
        }
    }

    result = normalize_balance_sheet(extracted)
    metric = result[0]["metrics"]["total_assets"]

    assert metric["value"] == 383266000000
    assert metric["source_accessions"] == ["SEC-001"]
    assert metric["source_form"] == "10-Q"


def test_balance_sheet_rejects_duplicates():
    observation = {
        "end": "2026-06-27",
        "val": 100,
        "accn": "SEC-001",
        "filed": "2026-07-31",
        "form": "10-Q",
    }
    extracted = {
        "total_assets": {
            "observations": [observation, observation.copy()],
        }
    }

    with pytest.raises(ValueError, match="Duplicate observation"):
        normalize_balance_sheet(extracted)


def test_cash_flow_provenance_and_missing_metrics():
    extracted = {
        "operating_cash_flow": {
            "quarterly_observations": [{
                "end": "2026-06-27",
                "start": "2026-03-29",
                "val": 34369000000,
                "derived": True,
                "calculation": "CUMULATIVE_DIFFERENCE",
                "source_accessions": ["SEC-001", "SEC-002"],
            }],
        },
        "common_stock_dividends": {
            "quarterly_observations": [],
        },
    }

    result = normalize_quarterly_cash_flow(extracted)
    metrics = result[0]["metrics"]

    assert metrics["operating_cash_flow"]["derived"] is True
    assert metrics["operating_cash_flow"]["source_accessions"] == [
        "SEC-001", "SEC-002"
    ]
    assert "common_stock_dividends" not in metrics


def test_cash_flow_rejects_duplicates():
    observation = {"end": "2026-06-27", "val": 100}
    extracted = {
        "operating_cash_flow": {
            "quarterly_observations": [
                observation,
                observation.copy(),
            ],
        }
    }

    with pytest.raises(ValueError, match="Duplicate observation"):
        normalize_quarterly_cash_flow(extracted)


def test_cash_flow_excludes_historical_dividend_only_periods():
    """Only operating-cash-flow reporting dates define quarterly periods."""
    from tools.financial_statements.normalization import (
        normalize_quarterly_cash_flow,
    )

    extracted = {
        "operating_cash_flow": {
            "concept": "NetCashProvidedByUsedInOperatingActivities",
            "quarterly_observations": [
                {
                    "end": "2026-06-27",
                    "val": 34369000000,
                    "source_accessions": ["accession-2026"],
                },
            ],
        },
        "common_stock_dividends": {
            "concept": "PaymentsOfDividendsCommonStock",
            "quarterly_observations": [
                {
                    "end": "2017-12-30",
                    "val": 3000000000,
                    "source_accessions": ["accession-2017"],
                },
            ],
        },
    }

    statements = normalize_quarterly_cash_flow(extracted)

    assert len(statements) == 1
    assert statements[0]["period_end"] == "2026-06-27"
    assert "operating_cash_flow" in statements[0]["metrics"]
    assert "common_stock_dividends" not in statements[0]["metrics"]

    # The original SEC observations must remain available.
    assert len(
        extracted["common_stock_dividends"]["quarterly_observations"]
    ) == 1
