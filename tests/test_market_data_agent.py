"""Integration tests for the LangGraph Market Data Agent."""

import pandas as pd
import pytest

from agents import market_data_agent as module


@pytest.fixture
def sample_prices():
    return pd.DataFrame(
        {
            "Close": [100.0, 105.0, 102.0, 110.0],
            "Open": [99.0, 104.0, 103.0, 109.0],
            "High": [101.0, 106.0, 104.0, 111.0],
            "Low": [98.0, 103.0, 101.0, 108.0],
            "Volume": [1000, 1200, 1100, 1500],
        },
        index=pd.date_range("2026-01-05", periods=4, freq="B"),
    )


def test_complete_agent_workflow(
    sample_prices, monkeypatch, tmp_path
):
    def mock_prices(ticker):
        assert ticker == "AAPL"
        return sample_prices.copy()

    def mock_charts(data, ticker):
        assert ticker == "AAPL"
        assert "Daily_Return" in data.columns
        return {"price": str(tmp_path / "price.html")}

    monkeypatch.setattr(
        module, "get_stock_prices", mock_prices
    )
    monkeypatch.setattr(
        module, "generate_market_charts", mock_charts
    )

    result = module.market_data_agent.invoke(
        {"ticker": "aapl"}
    )

    assert result["ticker"] == "AAPL"
    assert result["first_date"] == "2026-01-05"
    assert result["latest_date"] == "2026-01-08"
    assert result["statistics"]["observations"] == 3
    assert result["statistics"]["cumulative_return"] == (
        pytest.approx(0.10)
    )
    assert "price" in result["charts"]


def test_agent_propagates_market_data_errors(monkeypatch):
    def mock_failure(ticker):
        raise ValueError("No market data available")

    monkeypatch.setattr(
        module, "get_stock_prices", mock_failure
    )

    with pytest.raises(
        ValueError, match="No market data available"
    ):
        module.market_data_agent.invoke(
            {"ticker": "INVALID"}
        )
