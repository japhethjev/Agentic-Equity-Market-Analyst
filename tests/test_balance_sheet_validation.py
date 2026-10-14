"""Tests for balance-sheet reconciliation and provenance."""

from decimal import Decimal

from tools.financial_statements.balance_sheet_validation import (
    validate_balance_sheet,
)


def metric(value, end="2026-06-27", accn="filing-001"):
    return {
        "observations": [
            {"val": value, "end": end, "accn": accn}
        ]
    }


def sample_balance_sheet():
    return {
        "total_assets": metric(383266),
        "total_liabilities": metric(275746),
        "shareholders_equity": metric(107520),
        "long_term_debt": metric(82300),
        "current_portion_long_term_debt": metric(11007),
        "noncurrent_long_term_debt": metric(71340),
    }


def test_accounting_equation_passes():
    result = validate_balance_sheet(sample_balance_sheet())

    assert result["accounting_equation"] == "pass"
    assert result["reporting_dates_aligned"] is True
    assert result["filings_aligned"] is True


def test_accounting_equation_failure():
    data = sample_balance_sheet()
    data["shareholders_equity"] = metric(100000)

    result = validate_balance_sheet(data)

    assert result["accounting_equation"] == "fail"


def test_mismatched_reporting_dates():
    data = sample_balance_sheet()
    data["shareholders_equity"] = metric(
        107520, end="2026-03-28"
    )

    result = validate_balance_sheet(data)

    assert result["reporting_dates_aligned"] is False
    assert result["accounting_equation"] == "unavailable"


def test_mismatched_filing_references():
    data = sample_balance_sheet()
    data["shareholders_equity"] = metric(
        107520, accn="different-filing"
    )

    result = validate_balance_sheet(data)

    assert result["filings_aligned"] is False
    assert result["accounting_equation"] == "unavailable"


def test_debt_discrepancy_flagged():
    result = validate_balance_sheet(sample_balance_sheet())

    assert result["debt_reconciliation"] == "review_required"
    assert result["debt_difference"] == Decimal("47")


def test_debt_reconciliation_passes():
    data = sample_balance_sheet()
    data["long_term_debt"] = metric(82347)

    result = validate_balance_sheet(data)

    assert result["debt_reconciliation"] == "pass"
    assert result["debt_difference"] == Decimal("0")


def test_missing_data_not_assumed_zero():
    data = sample_balance_sheet()
    del data["total_assets"]

    result = validate_balance_sheet(data)

    assert result["accounting_equation"] == "unavailable"


def test_mismatched_debt_filings():
    data = sample_balance_sheet()
    data["long_term_debt"] = metric(
        82300, accn="different-filing"
    )

    result = validate_balance_sheet(data)

    assert result["debt_reconciliation"] == "unavailable"
    assert result["debt_difference"] is None
