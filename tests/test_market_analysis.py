"""Automated tests for equity return calculations and charts."""

import numpy as np
import pandas as pd
import pytest

from tools.return_calculator import (
    calculate_returns,
    calculate_performance_statistics,
)
from tools.chart_generator import generate_market_charts


@pytest.fixture
def sample_prices():
    dates = pd.date_range("2026-01-05", periods=4, freq="B")
    return pd.DataFrame(
        {"Close": [100.0, 110.0, 99.0, 108.9]},
        index=dates,
    )


def test_daily_simple_returns(sample_prices):
    result = calculate_returns(sample_prices)

    assert np.isnan(result["Daily_Return"].iloc[0])
    assert result["Daily_Return"].iloc[1] == pytest.approx(0.10)
    assert result["Daily_Return"].iloc[2] == pytest.approx(-0.10)
    assert result["Daily_Return"].iloc[3] == pytest.approx(0.10)


def test_logarithmic_returns(sample_prices):
    result = calculate_returns(sample_prices)

    assert result["Log_Return"].iloc[1] == pytest.approx(
        np.log(1.10)
    )


def test_cumulative_returns(sample_prices):
    result = calculate_returns(sample_prices)

    assert result["Cumulative_Return"].iloc[-1] == pytest.approx(
        0.089
    )


def test_annualised_volatility(sample_prices):
    result = calculate_returns(sample_prices)
    stats = calculate_performance_statistics(result)

    expected = np.std(
        [0.10, -0.10, 0.10], ddof=1
    ) * np.sqrt(252)

    assert stats["annualised_volatility"] == pytest.approx(
        expected
    )


def test_invalid_closing_prices(sample_prices):
    sample_prices.loc[sample_prices.index[1], "Close"] = 0

    with pytest.raises(ValueError):
        calculate_returns(sample_prices)


def test_chart_generation(sample_prices, tmp_path):
    result = calculate_returns(sample_prices)

    charts = generate_market_charts(
        result,
        "TEST",
        output_dir=str(tmp_path),
    )

    assert len(charts) == 3

    for path in charts.values():
        assert pd.io.common.file_exists(path)
