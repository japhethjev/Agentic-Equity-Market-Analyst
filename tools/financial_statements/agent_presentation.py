"""Prepare investor-ready financial statement tables."""

from tools.financial_statements.presentation import (
    format_financial_statement_table,
)


STATEMENT_TYPES = {
    "annual_income": "annual_income_statements",
    "quarterly_income": "quarterly_income_statements",
    "ttm_income": "ttm_income_statements",
    "balance_sheet": "balance_sheets",
    "quarterly_cash_flow": "quarterly_cash_flows",
}


def prepare_financial_statement_tables(state: dict) -> dict:
    """Format available statements with metrics as rows."""
    tables = {}

    for table_name, state_key in STATEMENT_TYPES.items():
        statements = state.get(state_key, [])

        if not statements:
            continue

        metrics = list(statements[0]["metrics"])
        tables[table_name] = format_financial_statement_table(
            statements, metrics
        )

    if state.get("ttm_cash_flows"):
        tables["ttm_cash_flow"] = format_ttm_cash_flow_table(state)

    return tables


def format_ttm_cash_flow_table(state: dict) -> dict:
    """Present TTM cash flows using the standard table formatter."""
    statements = []

    for statement in state["ttm_cash_flows"]:
        metrics = {}

        for name, record in statement["metrics"].items():
            metrics[name] = {
                "value": (
                    record["ttm"]
                    if record.get("status") == "available"
                    else None
                )
            }

        statements.append({
            "period_end": statement["period_end"],
            "metrics": metrics,
        })

    metric_order = list(statements[0]["metrics"]) if statements else []

    return format_financial_statement_table(
        statements, metric_order
    )
