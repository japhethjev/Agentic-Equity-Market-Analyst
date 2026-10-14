"""Tests for quarterly EPS and share validation."""

from decimal import Decimal

from tools.financial_statements.per_share_validation import (
    validate_quarterly_per_share,
)


def record(value, derived=False):
    return {
        "value": Decimal(str(value)),
        "derived": derived,
        "source_accessions": ["0000320193-25-000079"],
        "source_filed": ["2025-10-31"],
    }


def valid_statement():
    return {
        "period_end": "2025-09-27",
        "metrics": {
            "net_income": record(27466000000),
            "basic_eps": record("1.85", derived=False),
            "diluted_eps": record("1.85", derived=False),
            "basic_weighted_average_shares": record(14815306000),
            "diluted_weighted_average_shares": record(14863610000),
        },
    }


def test_valid_reported_per_share_metrics():
    result = validate_quarterly_per_share(valid_statement())

    assert result["status"] == "validated"
    assert result["checks"]["positive_shares"] == "pass"
    assert result["checks"]["diluted_shares"] == "pass"
    assert result["checks"]["provenance"] == "pass"


def test_missing_eps_requires_review():
    statement = valid_statement()
    del statement["metrics"]["basic_eps"]

    result = validate_quarterly_per_share(statement)

    assert result["status"] == "review_required"
    assert result["checks"]["completeness"] == "missing_data"


def test_reconstructed_eps_matches_net_income_and_shares():
    statement = valid_statement()
    metrics = statement["metrics"]

    for eps_name, shares_name in (
        ("basic_eps", "basic_weighted_average_shares"),
        ("diluted_eps", "diluted_weighted_average_shares"),
    ):
        metrics[eps_name]["derived"] = True
        metrics[eps_name]["value"] = (
            metrics["net_income"]["value"]
            / metrics[shares_name]["value"]
        )

    result = validate_quarterly_per_share(statement)

    assert result["status"] == "validated"
    assert result["checks"]["basic_eps"] == "pass"
    assert result["checks"]["diluted_eps"] == "pass"


def test_incorrect_reconstructed_eps_requires_review():
    statement = valid_statement()
    statement["metrics"]["basic_eps"]["derived"] = True
    statement["metrics"]["basic_eps"]["value"] = Decimal("9.99")

    result = validate_quarterly_per_share(statement)

    assert result["status"] == "review_required"
    assert result["checks"]["basic_eps"] == "review_required"


def test_zero_weighted_average_shares_requires_review():
    statement = valid_statement()
    statement["metrics"]["basic_weighted_average_shares"]["value"] = 0

    result = validate_quarterly_per_share(statement)

    assert result["status"] == "review_required"
    assert result["checks"]["positive_shares"] == "review_required"


def test_diluted_shares_below_basic_requires_review():
    statement = valid_statement()
    statement["metrics"]["diluted_weighted_average_shares"]["value"] = (
        Decimal("14000000000")
    )

    result = validate_quarterly_per_share(statement)

    assert result["status"] == "review_required"
    assert result["checks"]["diluted_shares"] == "review_required"


def test_missing_sec_provenance_requires_review():
    statement = valid_statement()
    statement["metrics"]["basic_eps"]["source_accessions"] = []

    result = validate_quarterly_per_share(statement)

    assert result["status"] == "review_required"
    assert result["checks"]["provenance"] == "review_required"


def test_negative_earnings_uses_basic_shares_for_diluted_eps():
    statement = valid_statement()
    metrics = statement["metrics"]

    metrics["net_income"]["value"] = Decimal("-1000000000")
    basic_shares = metrics["basic_weighted_average_shares"]["value"]

    metrics["basic_eps"]["derived"] = True
    metrics["diluted_eps"]["derived"] = True

    expected_eps = (
        metrics["net_income"]["value"] / basic_shares
    )

    metrics["basic_eps"]["value"] = expected_eps
    metrics["diluted_eps"]["value"] = expected_eps

    result = validate_quarterly_per_share(statement)

    assert result["status"] == "validated"
    assert result["checks"]["basic_eps"] == "pass"
    assert result["checks"]["diluted_eps"] == "pass"
