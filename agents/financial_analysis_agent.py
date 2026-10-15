"""LangGraph workflow for financial ratio analysis."""

from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from tools.financial_analysis.liquidity_history import build_liquidity_history
from tools.financial_analysis.liquidity_validation import validate_liquidity_history
from tools.financial_analysis.liquidity_presentation import prepare_liquidity_tables

from tools.financial_analysis.profitability_presentation import prepare_profitability_tables
from tools.financial_analysis.profitability_validation import validate_profitability_history

from tools.financial_analysis.profitability_history import (
    build_profitability_history,
)


class FinancialAnalysisState(TypedDict, total=False):
    ticker: str
    annual_income_statements: list[dict]
    quarterly_income_statements: list[dict]
    ttm_income_statements: list[dict]
    balance_sheets: list[dict]
    annual_cash_flows: list[dict]
    quarterly_cash_flows: list[dict]
    ttm_cash_flows: list[dict]
    liquidity: dict
    liquidity_validation: dict
    liquidity_tables: dict
    profitability: dict
    validation: dict
    tables: dict


def calculate_profitability(state: FinancialAnalysisState) -> dict:
    """Calculate historical profitability across reporting frequencies."""
    balance_sheets = state["balance_sheets"]

    return {
        "profitability": {
            period: build_profitability_history(
                state[f"{period}_income_statements"],
                balance_sheets,
                period,
            )
            for period in ("annual", "quarterly", "ttm")
        }
    }



def validate_profitability(state: FinancialAnalysisState) -> dict:
    """Validate calculated profitability ratios."""
    return {
        "validation": validate_profitability_history(
            state["profitability"]
        )
    }



def present_profitability(state: FinancialAnalysisState) -> dict:
    """Prepare annual, quarterly and TTM profitability matrices."""
    return {
        "tables": prepare_profitability_tables(
            state["profitability"]
        )
    }



def calculate_liquidity(state: FinancialAnalysisState) -> dict:
    """Calculate historical liquidity across reporting frequencies."""
    balance_sheets = state["balance_sheets"]
    quarterly_cash_flows = state["quarterly_cash_flows"]

    liquidity = {}

    for period in ("annual", "quarterly", "ttm"):
        liquidity[period] = build_liquidity_history(
            state[f"{period}_cash_flows"],
            balance_sheets,
            period,
            quarterly_cash_flows=quarterly_cash_flows,
        )

    return {"liquidity": liquidity}



def validate_liquidity(state: FinancialAnalysisState) -> dict:
    """Validate annual, quarterly and TTM liquidity ratios."""
    return {
        "liquidity_validation": validate_liquidity_history(
            state["liquidity"]
        )
    }


def present_liquidity(state: FinancialAnalysisState) -> dict:
    """Prepare investor-facing liquidity ratio matrices."""
    return {
        "liquidity_tables": prepare_liquidity_tables(
            state["liquidity"]
        )
    }


def build_financial_analysis_agent():
    """Compile the initial financial analysis workflow."""
    graph = StateGraph(FinancialAnalysisState)

    graph.add_node("calculate_profitability", calculate_profitability)
    graph.add_node("validate_profitability", validate_profitability)
    graph.add_node("present_profitability", present_profitability)

    graph.add_node("calculate_liquidity", calculate_liquidity)
    graph.add_node("validate_liquidity", validate_liquidity)
    graph.add_node("present_liquidity", present_liquidity)

    graph.add_edge(START, "calculate_profitability")
    graph.add_edge("calculate_profitability", "validate_profitability")
    graph.add_edge("validate_profitability", "present_profitability")
    graph.add_edge("present_profitability", "calculate_liquidity")
    graph.add_edge("calculate_liquidity", "validate_liquidity")
    graph.add_edge("validate_liquidity", "present_liquidity")
    graph.add_edge("present_liquidity", END)

    return graph.compile()


financial_analysis_agent = build_financial_analysis_agent()
