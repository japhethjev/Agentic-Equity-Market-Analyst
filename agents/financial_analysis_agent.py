"""LangGraph workflow for financial ratio analysis."""

from typing import TypedDict

from langgraph.graph import StateGraph, START, END

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


def build_financial_analysis_agent():
    """Compile the initial financial analysis workflow."""
    graph = StateGraph(FinancialAnalysisState)

    graph.add_node("calculate_profitability", calculate_profitability)
    graph.add_node("validate_profitability", validate_profitability)
    graph.add_node("present_profitability", present_profitability)

    graph.add_edge(START, "calculate_profitability")
    graph.add_edge("calculate_profitability", "validate_profitability")
    graph.add_edge("validate_profitability", "present_profitability")
    graph.add_edge("present_profitability", END)

    return graph.compile()


financial_analysis_agent = build_financial_analysis_agent()
