"""Consolidated validation for the Financial Statements Agent."""

from tools.financial_statements.income_statement_validation import (
    validate_annual_income_statement,
)
from tools.financial_statements.complete_quarterly_validation import (
    validate_complete_quarterly_income_statement,
)


def validate_agent_income_statements(state: dict) -> dict:
    """Validate annual and quarterly income statements."""
    annual = [
        validate_annual_income_statement(statement)
        for statement in state["annual_income_statements"]
    ]

    quarterly = [
        validate_complete_quarterly_income_statement(statement)
        for statement in state["quarterly_income_statements"]
    ]

    return {
        "annual_income": annual,
        "quarterly_income": quarterly,
    }


def validate_agent_balance_sheets(state: dict) -> list[dict]:
    """Validate the accounting equation for each reporting period."""
    from decimal import Decimal, InvalidOperation

    results = []
    required = (
        "total_assets",
        "total_liabilities",
        "shareholders_equity",
    )

    for statement in state["balance_sheets"]:
        metrics = statement["metrics"]

        if not all(name in metrics for name in required):
            status = "missing_data"
        else:
            try:
                assets, liabilities, equity = (
                    Decimal(str(metrics[name]["value"]))
                    for name in required
                )
                status = (
                    "pass"
                    if all(v.is_finite() for v in (assets, liabilities, equity))
                    and assets == liabilities + equity
                    else "review_required"
                )
            except (InvalidOperation, TypeError, ValueError, KeyError):
                status = "review_required"

        results.append({
            "period_end": statement["period_end"],
            "status": status,
        })

    return results


def validate_agent_ttm_cash_flows(state: dict) -> list[dict]:
    """Reconcile rolling TTM cash flows against quarterly observations."""
    from decimal import Decimal, InvalidOperation

    quarterly = {
        statement["period_end"]: statement["metrics"]
        for statement in state["quarterly_cash_flows"]
    }
    results = []

    for statement in state["ttm_cash_flows"]:
        for name, record in statement["metrics"].items():
            status = record.get("status")

            if status == "insufficient_data":
                result = "insufficient_data"
            elif status != "available":
                result = "review_required"
            else:
                dates = record.get("quarters_used", [])

                try:
                    assert len(dates) == 4
                    assert len(set(dates)) == 4
                    assert dates[0] == statement["period_end"]

                    total = sum(
                        (
                            Decimal(str(quarterly[date][name]["value"]))
                            for date in dates
                        ),
                        Decimal("0"),
                    )
                    expected = Decimal(str(record["ttm"]))

                    result = (
                        "pass"
                        if total.is_finite()
                        and expected.is_finite()
                        and total == expected
                        else "review_required"
                    )
                except (
                    AssertionError, KeyError, TypeError,
                    ValueError, InvalidOperation,
                ):
                    result = "review_required"

            results.append({
                "period_end": statement["period_end"],
                "metric": name,
                "status": result,
            })

    return results


def validate_all_financial_statements(state: dict) -> dict:
    """Run all statement checks and summarize their outcomes."""
    income = validate_agent_income_statements(state)
    balance = validate_agent_balance_sheets(state)
    cash = validate_agent_ttm_cash_flows(state)

    results = (
        income["annual_income"]
        + income["quarterly_income"]
        + balance
        + cash
    )

    passed = sum(
        item["status"] in {"validated", "pass"}
        for item in results
    )
    missing = sum(
        item["status"] in {"insufficient_data", "missing_data"}
        for item in results
    )
    failed = len(results) - passed - missing

    status = (
        "review_required" if failed
        else "validated_with_gaps" if missing
        else "validated"
    )

    return {
        "status": status,
        "checks_passed": passed,
        "checks_missing": missing,
        "checks_failed": failed,
        "annual_income": income["annual_income"],
        "quarterly_income": income["quarterly_income"],
        "balance_sheets": balance,
        "ttm_cash_flows": cash,
    }
