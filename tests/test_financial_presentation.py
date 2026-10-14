"""Regression tests for financial statement presentation."""

from copy import deepcopy
from decimal import Decimal

from tools.financial_statements.presentation import (
    format_financial_statement_table,
)


def test_periods_as_columns_newest_first():
    statements = [
        {"period_end": "2024-12-31", "metrics": {
            "revenue": {"value": Decimal("100000000")}
        }},
        {"period_end": "2025-12-31", "metrics": {
            "revenue": {"value": Decimal("200000000")}
        }},
    ]

    original = deepcopy(statements)
    table = format_financial_statement_table(statements, ["revenue"])

    assert table["periods"] == ["2025-12-31", "2024-12-31"]
    assert table["rows"][0]["values"] == ["200", "100"]
    assert statements == original


def test_missing_metrics_remain_missing():
    statements = [
        {"period_end": "2025-12-31", "metrics": {}}
    ]

    table = format_financial_statement_table(statements, ["net_income"])

    assert table["rows"][0]["values"] == [None]


def test_eps_and_shares_units():
    statements = [
        {"period_end": "2025-12-31", "metrics": {
            "basic_eps": {"value": Decimal("7.456")},
            "basic_weighted_average_shares": {
                "value": Decimal("15000000000")
            },
        }}
    ]

    table = format_financial_statement_table(
        statements,
        ["basic_eps", "basic_weighted_average_shares"],
    )

    assert table["rows"][0]["values"] == ["7.46"]
    assert table["rows"][0]["unit"] == "USD/share"
    assert table["rows"][1]["values"] == ["15,000.00"]
    assert table["rows"][1]["unit"] == "millions"
