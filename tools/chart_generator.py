"""Generate interactive equity market charts."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


def generate_market_charts(
    data: pd.DataFrame,
    ticker: str,
    output_dir: str = "charts",
) -> dict:
    """Create price, daily return and cumulative return charts."""

    required = {"Close", "Daily_Return", "Cumulative_Return"}

    if data.empty or not required.issubset(data.columns):
        raise ValueError("Missing or invalid market data.")

    ticker = ticker.strip().upper()

    if not ticker or not all(
        c.isascii() and (c.isalnum() or c in ".-")
        for c in ticker
    ):
        raise ValueError("Invalid ticker.")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    specifications = {
        "price": ("Close", "Adjusted Closing Price", 1),
        "daily_returns": ("Daily_Return", "Daily Return (%)", 100),
        "cumulative_returns": (
            "Cumulative_Return", "Cumulative Return (%)", 100
        ),
    }

    paths = {}

    for name, (column, ylabel, multiplier) in specifications.items():
        values = data[column] * multiplier

        if name == "daily_returns":
            trace = go.Bar(x=data.index, y=values, name=ylabel)
        else:
            trace = go.Scatter(
                x=data.index, y=values,
                mode="lines", name=ylabel
            )

        fig = go.Figure(data=[trace])

        fig.update_layout(
            title=f"{ticker} — {ylabel}",
            xaxis_title="Trading Date",
            yaxis_title=ylabel,
            template="plotly_white",
            hovermode="x unified",
        )

        filepath = output / f"{ticker}_{name}.html"
        fig.write_html(str(filepath), include_plotlyjs=True)

        paths[name] = str(filepath)

    return paths
