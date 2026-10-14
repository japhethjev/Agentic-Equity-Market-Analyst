"""Regression tests for quarterly income-statement validation."""

from decimal import Decimal

from tools.financial_statements.income_statement_quarterly_validation import (
    validate_quarterly_income_statement,
)


def make_statement(derived=False):
    sources = ["annual-001", "nine-month-001"] if derived else ["quarter-001"]

    values = {
        "revenue": 1000,
        "cost_of_revenue": 400,
        "gross_profit": 600,
        "operating_expenses": 200,
        "research_and_development": 120,
        "selling_general_administrative": 80,
        "operating_income": 400,
        "pretax_income": 350,
        "income_tax_expense": 50,
        "net_income": 300,
    }

    return {
        "period_end": "2025-09-27",
        "period_type": "quarterly",
        "metrics": {
            name: {
                "value": Decimal(value),
                "period_start": "2025-06-29",
                "derived": derived,
                "source_accessions": sources.copy(),
            }
            for name, value in values.items()
        },
    }


def test_valid_reported_quarter():
    result = validate_quarterly_income_statement(make_statement())
    assert result["status"] == "validated"
    assert result["metrics_count"] == 10


def test_valid_reconstructed_fourth_quarter():
    result = validate_quarterly_income_statement(make_statement(True))
    assert result["status"] == "validated"
    assert result["provenance_status"] == "consistent"


def test_gross_profit_discrepancy():
    statement = make_statement()
    statement["metrics"]["gross_profit"]["value"] = Decimal(590)

    result = validate_quarterly_income_statement(statement)

    assert result["status"] == "review_required"
    assert result["differences"]["gross_profit"] == Decimal(10)


def test_operating_expenses_discrepancy():
    statement = make_statement()
    statement["metrics"]["operating_expenses"]["value"] = Decimal(210)

    result = validate_quarterly_income_statement(statement)

    assert result["checks"]["operating_expenses"] == "review_required"


def test_missing_metric():
    statement = make_statement()
    del statement["metrics"]["net_income"]

    result = validate_quarterly_income_statement(statement)

    assert result["status"] == "review_required"
    assert result["checks"]["net_income"] == "missing_data"


def test_invalid_numeric_value():
    statement = make_statement()
    statement["metrics"]["revenue"]["value"] = "invalid"

    result = validate_quarterly_income_statement(statement)

    assert result["checks"]["gross_profit"] == "invalid_data"
    assert result["status"] == "review_required"


def test_nonfinite_value():
    statement = make_statement()
    statement["metrics"]["revenue"]["value"] = Decimal("NaN")

    result = validate_quarterly_income_statement(statement)

    assert result["checks"]["gross_profit"] == "invalid_data"


def test_mixed_reporting_periods():
    statement = make_statement()
    statement["metrics"]["revenue"]["period_start"] = "2025-06-28"

    result = validate_quarterly_income_statement(statement)

    assert result["period_status"] == "review_required"
    assert result["status"] == "review_required"


def test_mixed_filing_accessions():
    statement = make_statement()
    statement["metrics"]["revenue"]["source_accessions"] = ["other-001"]

    result = validate_quarterly_income_statement(statement)

    assert result["provenance_status"] == "review_required"


def test_missing_source_accession():
    statement = make_statement()
    statement["metrics"]["revenue"]["source_accessions"] = []

    result = validate_quarterly_income_statement(statement)

    assert result["provenance_status"] == "review_required"


def test_incorrect_reconstructed_sources():
    statement = make_statement(True)
    statement["metrics"]["revenue"]["source_accessions"] = ["annual-001"]

    result = validate_quarterly_income_statement(statement)

    assert result["provenance_status"] == "review_required"


def test_empty_statement():
    result = validate_quarterly_income_statement({
        "period_end": "2025-09-27",
        "metrics": {},
    })

    assert result["status"] == "review_required"
    assert result["metrics_count"] == 0
