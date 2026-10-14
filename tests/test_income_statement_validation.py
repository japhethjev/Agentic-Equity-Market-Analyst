"""Tests for annual income-statement validation."""

from decimal import Decimal

from tools.financial_statements.income_statement_validation import (
    validate_annual_income_statement,
)


def metric(value, accession="filing-001"):
    return {
        "value": Decimal(str(value)),
        "source_accession": accession,
    }


def valid_statement():
    return {
        "period_end": "2025-09-27",
        "period_type": "annual",
        "metrics": {
            "revenue": metric(1000),
            "cost_of_revenue": metric(400),
            "gross_profit": metric(600),
            "operating_expenses": metric(200),
            "operating_income": metric(400),
            "pretax_income": metric(350),
            "income_tax_expense": metric(50),
            "net_income": metric(300),
        },
    }


def test_valid_statement():
    result = validate_annual_income_statement(valid_statement())

    assert result["status"] == "validated"
    assert result["provenance_status"] == "consistent"
    assert all(value == "pass" for value in result["checks"].values())


def test_gross_profit_discrepancy():
    statement = valid_statement()
    statement["metrics"]["gross_profit"]["value"] = Decimal("590")

    result = validate_annual_income_statement(statement)

    assert result["status"] == "review_required"
    assert result["checks"]["gross_profit"] == "review_required"
    assert result["differences"]["gross_profit"] == Decimal("10")


def test_operating_income_discrepancy():
    statement = valid_statement()
    statement["metrics"]["operating_income"]["value"] = Decimal("390")

    result = validate_annual_income_statement(statement)

    assert result["checks"]["operating_income"] == "review_required"


def test_net_income_discrepancy():
    statement = valid_statement()
    statement["metrics"]["net_income"]["value"] = Decimal("290")

    result = validate_annual_income_statement(statement)

    assert result["checks"]["net_income"] == "review_required"


def test_missing_metric():
    statement = valid_statement()
    del statement["metrics"]["income_tax_expense"]

    result = validate_annual_income_statement(statement)

    assert result["status"] == "review_required"
    assert result["checks"]["net_income"] == "missing_data"


def test_mixed_filing_accessions():
    statement = valid_statement()
    statement["metrics"]["revenue"]["source_accession"] = "filing-002"

    result = validate_annual_income_statement(statement)

    assert result["provenance_status"] == "review_required"
    assert result["status"] == "review_required"


def test_missing_accession():
    statement = valid_statement()
    statement["metrics"]["revenue"]["source_accession"] = None

    result = validate_annual_income_statement(statement)

    assert result["provenance_status"] == "review_required"


def test_empty_statement():
    result = validate_annual_income_statement({
        "period_end": "2025-09-27",
        "metrics": {},
    })

    assert result["status"] == "review_required"
    assert result["provenance_status"] == "review_required"
    assert all(
        value == "missing_data"
        for value in result["checks"].values()
    )


def test_source_accession_preserved():
    result = validate_annual_income_statement(valid_statement())

    assert result["source_accessions"] == ["filing-001"]
