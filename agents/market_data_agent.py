"""LangGraph workflow for equity market-data analysis."""

from typing import TypedDict

import pandas as pd
from langgraph.graph import StateGraph, START, END

from tools.market_data import get_stock_prices
from tools.return_calculator import (
    calculate_returns,
    calculate_performance_statistics,
)
from tools.chart_generator import generate_market_charts


class MarketDataState(TypedDict, total=False):
    ticker: str
    prices: pd.DataFrame
    returns: pd.DataFrame
    statistics: dict
    charts: dict
    first_date: str
    latest_date: str


def retrieve_prices(state: MarketDataState) -> dict:
    ticker = state["ticker"].strip().upper()
    prices = get_stock_prices(ticker)

    return {
        "ticker": ticker,
        "prices": prices,
        "first_date": str(prices.index.min().date()),
        "latest_date": str(prices.index.max().date()),
    }


def analyse_returns(state: MarketDataState) -> dict:
    results = calculate_returns(state["prices"])
    statistics = calculate_performance_statistics(results)

    return {
        "returns": results,
        "statistics": statistics,
    }


def create_charts(state: MarketDataState) -> dict:
    charts = generate_market_charts(
        state["returns"],
        state["ticker"],
    )

    return {"charts": charts}


def build_market_data_agent():
    graph = StateGraph(MarketDataState)

    graph.add_node("retrieve_prices", retrieve_prices)
    graph.add_node("analyse_returns", analyse_returns)
    graph.add_node("create_charts", create_charts)

    graph.add_edge(START, "retrieve_prices")
    graph.add_edge("retrieve_prices", "analyse_returns")
    graph.add_edge("analyse_returns", "create_charts")
    graph.add_edge("create_charts", END)

    return graph.compile()


market_data_agent = build_market_data_agent()


if __name__ == "__main__":
    result = market_data_agent.invoke({"ticker": "AAPL"})

    print("\nMARKET DATA AGENT EXECUTION SUCCESSFUL")
    print("Ticker:", result["ticker"])
    print("First date:", result["first_date"])
    print("Latest date:", result["latest_date"])

    print("\nPERFORMANCE STATISTICS")
    for key, value in result["statistics"].items():
        if key == "observations":
            print(f"{key}: {value}")
        else:
            print(f"{key}: {value:.2%}")

    print("\nGENERATED CHARTS")
    for name, path in result["charts"].items():
        print(f"{name}: {path}")
