"""Validate quarterly income-statement accounting and provenance."""

from decimal import Decimal, InvalidOperation


CHECKS = {
    "gross_profit": (
        "revenue", "cost_of_revenue", "gross_profit", "subtract"
    ),
    "operating_income": (
        "gross_profit", "operating_expenses", "operating_income", "subtract"
    ),
    "operating_expenses": (
        "research_and_development",
        "selling_general_administrative",
        "operating_expenses",
        "add",
    ),
    "net_income": (
        "pretax_income", "income_tax_expense", "net_income", "subtract"
    ),
}


def validate_quarterly_income_statement(statement: dict) -> dict:
    """Check accounting identities, reporting periods and SEC sources."""

    metrics = statement.get("metrics", {})
    checks = {}
    differences = {}

    for name, (first, second, reported, operation) in CHECKS.items():
        if not all(key in metrics for key in (first, second, reported)):
            checks[name] = "missing_data"
            differences[name] = None
            continue

        try:
            a = Decimal(str(metrics[first]["value"]))
            b = Decimal(str(metrics[second]["value"]))
            actual = Decimal(str(metrics[reported]["value"]))

            if not all(value.is_finite() for value in (a, b, actual)):
                raise InvalidOperation

            calculated = a + b if operation == "add" else a - b
            difference = calculated - actual

            differences[name] = difference
            checks[name] = (
                "pass" if difference == 0 else "review_required"
            )
        except (KeyError, TypeError, ValueError, InvalidOperation):
            checks[name] = "invalid_data"
            differences[name] = None

    starts = {
        record.get("period_start")
        for record in metrics.values()
    }

    period_status = (
        "consistent"
        if len(starts) == 1 and None not in starts and metrics
        else "review_required"
    )

    source_groups = set()
    source_valid = bool(metrics)

    for record in metrics.values():
        accessions = record.get("source_accessions")
        derived = record.get("derived", False)

        if (
            not isinstance(accessions, list)
            or len(accessions) != (2 if derived else 1)
            or any(not accession for accession in accessions)
        ):
            source_valid = False
            continue

        source_groups.add((derived, tuple(accessions)))

    provenance_status = (
        "consistent"
        if source_valid and len(source_groups) == 1
        else "review_required"
    )

    validated = (
        len(metrics) == 10
        and all(result == "pass" for result in checks.values())
        and period_status == "consistent"
        and provenance_status == "consistent"
    )

    return {
        "period_end": statement.get("period_end"),
        "status": "validated" if validated else "review_required",
        "checks": checks,
        "differences": differences,
        "period_status": period_status,
        "provenance_status": provenance_status,
        "metrics_count": len(metrics),
    }
