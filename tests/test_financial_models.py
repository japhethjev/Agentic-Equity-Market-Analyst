"""Tests for standardised financial statement models."""

from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from tools.financial_statements.models import FinancialMetric


@pytest.fixture
def valid_metric():
    return FinancialMetric(
        company_name="Example Corporation",
        ticker="EXAMPLE",
        metric_name="revenue",
        value=Decimal("125000000"),
        currency="USD",
        statement_type="income_statement",
        period_type="annual",
        period_end=date(2025, 12, 31),
        source_document="Annual Report 2025",
        source_page=42,
    )


def test_valid_financial_metric(valid_metric):
    assert valid_metric.metric_name == "revenue"
    assert valid_metric.value == Decimal("125000000")
    assert valid_metric.source_page == 42


def test_missing_company_name(valid_metric):
    with pytest.raises(ValueError, match="Company name"):
        replace(valid_metric, company_name="")


def test_missing_ticker(valid_metric):
    with pytest.raises(ValueError, match="Ticker"):
        replace(valid_metric, ticker="")


def test_missing_metric_name(valid_metric):
    with pytest.raises(ValueError, match="Metric name"):
        replace(valid_metric, metric_name="")


def test_invalid_currency(valid_metric):
    with pytest.raises(ValueError, match="Currency"):
        replace(valid_metric, currency="US")


def test_non_finite_value(valid_metric):
    with pytest.raises(ValueError, match="finite"):
        replace(valid_metric, value=Decimal("NaN"))


def test_missing_source_document(valid_metric):
    with pytest.raises(ValueError, match="Source document"):
        replace(valid_metric, source_document="")


def test_invalid_source_page(valid_metric):
    with pytest.raises(ValueError, match="Source page"):
        replace(valid_metric, source_page=0)
