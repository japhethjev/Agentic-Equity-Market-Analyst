"""Historical equity market-data retrieval and validation."""

import pandas as pd
import yfinance as yf


def get_stock_prices(
    ticker: str,
    start: str | None = None,
    end: str | None = None,
) -> pd.DataFrame:
    """
    Retrieve daily historical stock prices.

    Parameters
    ----------
    ticker : str
        Stock ticker, e.g. AAPL, MSFT, DANGCEM.LG.
    start : str
        Start date, YYYY-MM-DD (inclusive).
    end : str
        End date, YYYY-MM-DD (exclusive).

    Returns
    -------
    pd.DataFrame
        Validated daily OHLCV prices with a Date index.
    """
    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Ticker cannot be empty.")

    # Rolling 12-month window, including the current month.
    today = pd.Timestamp.now(tz="UTC").date()

    if start is None:
        start = (
            pd.Timestamp(today) - pd.DateOffset(months=12)
        ).date().isoformat()

    if end is None:
        # Yahoo Finance treats the end date as exclusive.
        end = (
            pd.Timestamp(today) + pd.Timedelta(days=1)
        ).date().isoformat()

    start_date = pd.Timestamp(start)
    end_date = pd.Timestamp(end)

    if start_date >= end_date:
        raise ValueError("Start date must be before end date.")

    data = yf.download(
        tickers=ticker,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=False,
    )

    if data.empty:
        raise ValueError(
            f"No market data returned for {ticker}."
        )

    # yfinance may return MultiIndex columns.
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    required_columns = [
        "Open", "High", "Low", "Close", "Volume"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing market-data columns: {missing_columns}"
        )

    data = data[required_columns].copy()
    data = data.sort_index()
    data = data[~data.index.duplicated(keep="last")]

    data = data.dropna(subset=["Close"])

    if data.empty:
        raise ValueError(
            f"No valid closing prices for {ticker}."
        )

    if (data["Close"] <= 0).any():
        raise ValueError(
            f"Invalid non-positive closing price for {ticker}."
        )

    data.index.name = "Date"

    return data
