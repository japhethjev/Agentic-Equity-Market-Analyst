"""Deterministic equity return and volatility calculations."""

import numpy as np
import pandas as pd


def calculate_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily simple, log and cumulative returns."""

    if "Close" not in prices.columns:
        raise ValueError("Price data must contain a Close column.")

    if prices.empty:
        raise ValueError("Price data cannot be empty.")

    data = prices.copy().sort_index()

    if data["Close"].isna().any():
        raise ValueError("Closing prices contain missing values.")

    if (data["Close"] <= 0).any():
        raise ValueError("Closing prices must be positive.")

    data["Daily_Return"] = data["Close"].pct_change()

    data["Log_Return"] = np.log(
        data["Close"] / data["Close"].shift(1)
    )

    data["Cumulative_Return"] = (
        data["Close"] / data["Close"].iloc[0] - 1
    )

    return data


def calculate_performance_statistics(
    data: pd.DataFrame,
) -> dict:
    """Calculate descriptive return and risk statistics."""

    returns = data["Daily_Return"].dropna()

    if len(returns) < 2:
        raise ValueError(
            "At least three closing prices are required."
        )

    return {
        "observations": len(returns),
        "mean_daily_return": float(returns.mean()),
        "daily_volatility": float(returns.std(ddof=1)),
        "annualised_volatility": float(
            returns.std(ddof=1) * np.sqrt(252)
        ),
        "cumulative_return": float(
            data["Cumulative_Return"].iloc[-1]
        ),
        "minimum_daily_return": float(returns.min()),
        "maximum_daily_return": float(returns.max()),
    }
