"""Validate complete 14-metric quarterly income statements."""

from tools.financial_statements.income_statement_quarterly_validation import (
    validate_quarterly_income_statement,
)
from tools.financial_statements.per_share_validation import (
    validate_quarterly_per_share,
)


MONETARY_METRICS = (
    "revenue",
    "cost_of_revenue",
    "gross_profit",
    "operating_expenses",
    "research_and_development",
    "selling_general_administrative",
    "operating_income",
    "pretax_income",
    "income_tax_expense",
    "net_income",
)


def validate_complete_quarterly_income_statement(statement: dict) -> dict:
    """Validate monetary accounts and per-share metrics independently."""

    metrics = statement.get("metrics", {})

    monetary_statement = {
        "period_end": statement.get("period_end"),
        "metrics": {
            name: metrics[name]
            for name in MONETARY_METRICS
            if name in metrics
        },
    }

    monetary = validate_quarterly_income_statement(
        monetary_statement
    )
    per_share = validate_quarterly_per_share(statement)

    period_starts = {
        record.get("period_start")
        for record in metrics.values()
    }

    period_status = (
        "consistent"
        if len(metrics) == 14
        and len(period_starts) == 1
        and None not in period_starts
        else "review_required"
    )

    source_groups = set()
    source_valid = len(metrics) == 14

    for record in metrics.values():
        accessions = record.get("source_accessions")
        filed = record.get("source_filed")
        derived = record.get("derived", False)

        if (
            not isinstance(accessions, list)
            or not isinstance(filed, list)
            or len(accessions) != (2 if derived else 1)
            or len(accessions) != len(filed)
            or any(not item for item in accessions + filed)
        ):
            source_valid = False
            continue

        source_groups.add(
            (derived, tuple(zip(accessions, filed)))
        )

    provenance_status = (
        "consistent"
        if source_valid and len(source_groups) == 1
        else "review_required"
    )

    validated = (
        len(metrics) == 14
        and provenance_status == "consistent"
        and monetary["status"] == "validated"
        and per_share["status"] == "validated"
        and period_status == "consistent"
    )

    return {
        "period_end": statement.get("period_end"),
        "status": "validated" if validated else "review_required",
        "metrics_count": len(metrics),
        "period_status": period_status,
        "provenance_status": provenance_status,
        "monetary_validation": monetary,
        "per_share_validation": per_share,
    }
