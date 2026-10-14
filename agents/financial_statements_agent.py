from tools.financial_statements.agent_presentation import prepare_financial_statement_tables
from tools.financial_statements.agent_validation import validate_all_financial_statements
from decimal import Decimal
from tools.financial_statements.income_statement_validation import validate_annual_income_statement
from tools.financial_statements.complete_quarterly_validation import validate_complete_quarterly_income_statement

"""LangGraph workflow for SEC financial statement analysis."""

from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from tools.financial_statements.sec_edgar import get_company_facts


from tools.financial_statements.income_statement_annual import (
    build_annual_income_statements,
)
from tools.financial_statements.income_statement_quarterly import (
    build_quarterly_income_statements,
)
from tools.financial_statements.income_statement_ttm import (
    build_ttm_income_statements,
)

from tools.financial_statements.balance_sheet import extract_balance_sheet
from tools.financial_statements.normalization import normalize_balance_sheet

from tools.financial_statements.cash_flow import extract_cash_flow
from tools.financial_statements.normalization import normalize_quarterly_cash_flow

from tools.financial_statements.cash_flow_ttm import calculate_cash_flow_ttm

class FinancialStatementsState(TypedDict, total=False):
    ticker: str
    cik: int
    company_facts: dict
    annual_income_statements: list[dict]
    quarterly_income_statements: list[dict]
    ttm_income_statements: list[dict]
    balance_sheets: list[dict]
    quarterly_cash_flows: list[dict]
    ttm_cash_flows: list[dict]
    extracted_cash_flows: dict
    tables: dict
    validation: dict


def retrieve_company_facts(state: FinancialStatementsState) -> dict:
    """Retrieve SEC company facts using the company's CIK."""
    cik = int(state["cik"])

    if cik <= 0:
        raise ValueError("CIK must be a positive integer")

    return {
        "cik": cik,
        "ticker": state["ticker"].strip().upper(),
        "company_facts": get_company_facts(cik),
    }



def construct_income_statements(state: FinancialStatementsState) -> dict:
    """Construct annual, quarterly and TTM income statements."""
    facts = state["company_facts"]

    annual = build_annual_income_statements(facts, years=5)
    quarterly = build_quarterly_income_statements(facts, quarters=12)
    ttm = build_ttm_income_statements(quarterly)

    return {
        "annual_income_statements": annual,
        "quarterly_income_statements": quarterly,
        "ttm_income_statements": ttm,
    }


def construct_balance_sheets(state: FinancialStatementsState) -> dict:
    """Extract and normalize SEC balance sheet observations."""
    extracted = extract_balance_sheet(
        state["company_facts"],
        periods=12,
    )
    return {
        "balance_sheets": normalize_balance_sheet(extracted),
    }


def construct_quarterly_cash_flows(
    state: FinancialStatementsState,
) -> dict:
    """Extract and normalize the latest 12 quarterly cash flow statements."""
    extracted = extract_cash_flow(
        state["company_facts"],
        quarters=12,
    )

    return {
        "quarterly_cash_flows": normalize_quarterly_cash_flow(extracted),
        "extracted_cash_flows": extracted,
    }


def construct_ttm_cash_flows(
    state: FinancialStatementsState,
) -> dict:
    """Calculate rolling TTM cash flows for available quarterly periods."""
    quarterly = state["quarterly_cash_flows"]
    extracted = state["extracted_cash_flows"]

    ttm_statements = []

    for statement in quarterly[:9]:
        period_end = statement["period_end"]
        metrics = calculate_cash_flow_ttm(extracted, period_end)

        ttm_statements.append({
            "period_end": period_end,
            "period_type": "ttm",
            "metrics": metrics,
        })

    return {"ttm_cash_flows": ttm_statements}



def validate_financial_statements(state: FinancialStatementsState) -> dict:
    """Validate all constructed financial statements."""
    return {
        "validation": validate_all_financial_statements(state)
    }



def present_financial_statements(state: FinancialStatementsState) -> dict:
    """Generate investor-ready financial statement tables."""
    return {
        "tables": prepare_financial_statement_tables(state)
    }


def build_financial_statements_agent():
    """Compile the initial financial statements workflow."""
    graph = StateGraph(FinancialStatementsState)

    graph.add_node("retrieve_company_facts", retrieve_company_facts)
    graph.add_node("construct_income_statements", construct_income_statements)

    graph.add_node("construct_balance_sheets", construct_balance_sheets)

    graph.add_node("construct_quarterly_cash_flows", construct_quarterly_cash_flows)

    graph.add_node("construct_ttm_cash_flows", construct_ttm_cash_flows)
    graph.add_node("validate_financial_statements", validate_financial_statements)
    graph.add_node("present_financial_statements", present_financial_statements)

    graph.add_edge(START, "retrieve_company_facts")
    graph.add_edge("retrieve_company_facts", "construct_income_statements")
    graph.add_edge("construct_income_statements", "construct_balance_sheets")
    graph.add_edge("construct_balance_sheets", "construct_quarterly_cash_flows")
    graph.add_edge("construct_quarterly_cash_flows", "construct_ttm_cash_flows")
    graph.add_edge("construct_ttm_cash_flows", "validate_financial_statements")
    graph.add_edge("validate_financial_statements", "present_financial_statements")
    graph.add_edge("present_financial_statements", END)

    return graph.compile()


financial_statements_agent = build_financial_statements_agent()
