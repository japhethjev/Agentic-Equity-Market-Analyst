"""Regression tests for complete quarterly income-statement validation."""

from tools.financial_statements.complete_quarterly_validation import (
    validate_complete_quarterly_income_statement,
)


def test_empty_statement_requires_review():
    statement = {
        "period_end": "2025-09-27",
        "metrics": {},
    }

    result = validate_complete_quarterly_income_statement(statement)

    assert result["status"] == "review_required"
    assert result["metrics_count"] == 0
    assert result["monetary_validation"]["status"] == "review_required"
    assert result["per_share_validation"]["status"] == "review_required"


def test_mismatched_per_share_period_requires_review(monkeypatch):
    from tools.financial_statements import complete_quarterly_validation as module

    monkeypatch.setattr(
        module,
        "validate_quarterly_income_statement",
        lambda statement: {"status": "validated"},
    )
    monkeypatch.setattr(
        module,
        "validate_quarterly_per_share",
        lambda statement: {"status": "validated"},
    )

    metrics = {
        f"metric_{index}": {
            "period_start": "2025-06-29",
        }
        for index in range(14)
    }

    metrics["metric_13"]["period_start"] = "2025-03-30"

    result = module.validate_complete_quarterly_income_statement(
        {
            "period_end": "2025-09-27",
            "metrics": metrics,
        }
    )

    assert result["status"] == "review_required"


def test_mismatched_sec_accessions_require_review(monkeypatch):
    from tools.financial_statements import complete_quarterly_validation as module

    monkeypatch.setattr(
        module,
        "validate_quarterly_income_statement",
        lambda statement: {"status": "validated"},
    )
    monkeypatch.setattr(
        module,
        "validate_quarterly_per_share",
        lambda statement: {"status": "validated"},
    )

    metrics = {
        f"metric_{index}": {
            "period_start": "2025-03-30",
            "derived": False,
            "source_accessions": ["0000320193-25-000073"],
            "source_filed": ["2025-08-01"],
        }
        for index in range(14)
    }

    metrics["metric_13"]["source_accessions"] = [
        "0000320193-25-000079"
    ]

    result = module.validate_complete_quarterly_income_statement(
        {"period_end": "2025-06-28", "metrics": metrics}
    )

    assert result["status"] == "review_required"
