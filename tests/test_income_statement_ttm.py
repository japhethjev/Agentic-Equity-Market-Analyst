"""Regression tests for rolling TTM income statements."""

from datetime import date
from decimal import Decimal

from tools.financial_statements.income_statement_quarterly import MONETARY_METRICS
from tools.financial_statements.income_statement_ttm import build_ttm_income_statements


def make_quarters():
    """Create four consecutive quarterly financial statements."""
    periods = [
        ("2025-01-01", "2025-03-31"),
        ("2025-04-01", "2025-06-30"),
        ("2025-07-01", "2025-09-30"),
        ("2025-10-01", "2025-12-31"),
    ]
    quarters = []

    for index, (start, end) in enumerate(periods):
        accession = f"test-accession-{index}"
        metrics = {}

        for name in MONETARY_METRICS:
            metrics[name] = {
                "value": Decimal("300"),
                "unit": "USD",
                "period_start": start,
                "source_accessions": [accession],
            }

        for name, shares in (
            ("basic_weighted_average_shares", 100 + index * 10),
            ("diluted_weighted_average_shares", 110 + index * 10),
        ):
            metrics[name] = {
                "value": Decimal(shares),
                "unit": "shares",
                "period_start": start,
                "source_accessions": [accession],
            }

        quarters.append({"period_end": end, "metrics": metrics})

    return quarters


def test_ttm_monetary_aggregation():
    results = build_ttm_income_statements(make_quarters())

    assert len(results) == 1

    statement = results[0]
    metrics = statement["metrics"]

    assert statement["period_start"] == "2025-01-01"
    assert statement["period_end"] == "2025-12-31"
    assert statement["period_type"] == "TTM"

    assert len(metrics) == 14

    for name in MONETARY_METRICS:
        assert metrics[name]["value"] == Decimal("1200")
        assert metrics[name]["unit"] == "USD"
        assert metrics[name]["calculation"] == "SUM_FOUR_QUARTERS"


def test_ttm_weighted_shares_and_eps():
    quarters = make_quarters()
    metrics = build_ttm_income_statements(quarters)[0]["metrics"]

    days = [
        (
            date.fromisoformat(q["period_end"])
            - date.fromisoformat(q["metrics"]["revenue"]["period_start"])
        ).days + 1
        for q in quarters
    ]

    total_days = Decimal(sum(days))

    expected_basic = sum(
        (Decimal(100 + i * 10) * days[i] for i in range(4)),
        Decimal("0"),
    ) / total_days

    expected_diluted = sum(
        (Decimal(110 + i * 10) * days[i] for i in range(4)),
        Decimal("0"),
    ) / total_days

    assert metrics["basic_weighted_average_shares"]["value"] == expected_basic
    assert metrics["diluted_weighted_average_shares"]["value"] == expected_diluted

    assert metrics["basic_eps"]["value"] == Decimal("1200") / expected_basic
    assert metrics["diluted_eps"]["value"] == Decimal("1200") / expected_diluted
    assert metrics["diluted_eps"]["value"] < metrics["basic_eps"]["value"]


def test_ttm_preserves_source_accessions():
    metrics = build_ttm_income_statements(make_quarters())[0]["metrics"]

    expected = {
        f"test-accession-{i}"
        for i in range(4)
    }

    for name in (
        "revenue",
        "net_income",
        "basic_weighted_average_shares",
        "diluted_weighted_average_shares",
        "basic_eps",
        "diluted_eps",
    ):
        assert set(metrics[name]["source_accessions"]) == expected


def test_ttm_requires_four_quarters():
    assert build_ttm_income_statements(make_quarters()[:3]) == []


def test_ttm_rejects_nonconsecutive_quarters():
    quarters = make_quarters()
    quarters[1]["metrics"]["revenue"]["period_start"] = "2025-04-02"

    assert build_ttm_income_statements(quarters) == []


def test_ttm_rejects_zero_weighted_shares():
    import pytest

    quarters = make_quarters()

    for quarter in quarters:
        quarter["metrics"]["basic_weighted_average_shares"]["value"] = Decimal("0")

    with pytest.raises(ValueError):
        build_ttm_income_statements(quarters)


def test_ttm_loss_uses_basic_shares_for_diluted_eps():
    quarters = make_quarters()

    for quarter in quarters:
        quarter["metrics"]["net_income"]["value"] = Decimal("-300")

    metrics = build_ttm_income_statements(quarters)[0]["metrics"]

    assert metrics["net_income"]["value"] == Decimal("-1200")
    assert metrics["diluted_eps"]["value"] == metrics["basic_eps"]["value"]
    assert metrics["basic_eps"]["value"] < 0
