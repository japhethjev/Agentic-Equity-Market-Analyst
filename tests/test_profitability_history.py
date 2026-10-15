"""Tests for historical profitability analysis."""

from decimal import Decimal

import pytest

from tools.financial_analysis.profitability_history import (
    build_profitability_history,
)


def make_statement(end, start=None):
    metrics = {
        "revenue": {"value": Decimal("100")},
        "gross_profit": {"value": Decimal("60")},
        "operating_income": {"value": Decimal("30")},
        "net_income": {"value": Decimal("20")},
    }

    if start:
        metrics["net_income"]["period_start"] = start

    return {"period_end": end, "metrics": metrics}


def test_history_orders_newest_first():
    statements = [
        make_statement("2024-12-31", "2024-01-01"),
        make_statement("2025-12-31", "2025-01-01"),
    ]

    result = build_profitability_history(statements, [], "annual")

    assert [r["period_end"] for r in result] == [
        "2025-12-31",
        "2024-12-31",
    ]
    assert result[0]["metrics"]["return_on_assets"]["status"] == (
        "insufficient_data"
    )


def test_missing_start_preserves_margins():
    result = build_profitability_history(
        [make_statement("2025-12-31")],
        [],
        "annual",
    )

    metrics = result[0]["metrics"]

    assert metrics["net_profit_margin"]["value"] == Decimal("20")
    assert metrics["return_on_assets"]["status"] == "insufficient_data"
    assert metrics["return_on_equity"]["status"] == "insufficient_data"


def test_rejects_unsupported_period():
    with pytest.raises(ValueError, match="Unsupported reporting period"):
        build_profitability_history([], [], "monthly")
