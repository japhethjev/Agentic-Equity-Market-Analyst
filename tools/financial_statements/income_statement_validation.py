"""Validate annual income-statement accounting identities and provenance."""

CHECKS = {
    "gross_profit": (
        "revenue",
        "cost_of_revenue",
        "gross_profit",
    ),
    "operating_income": (
        "gross_profit",
        "operating_expenses",
        "operating_income",
    ),
    "net_income": (
        "pretax_income",
        "income_tax_expense",
        "net_income",
    ),
}


def validate_annual_income_statement(statement: dict) -> dict:
    """Validate accounting identities and SEC filing consistency."""

    metrics = statement.get("metrics", {})
    results = {}
    differences = {}

    for name, (first, second, reported) in CHECKS.items():
        if not all(key in metrics for key in (first, second, reported)):
            results[name] = "missing_data"
            differences[name] = None
            continue

        calculated = metrics[first]["value"] - metrics[second]["value"]
        actual = metrics[reported]["value"]
        difference = calculated - actual

        differences[name] = difference
        results[name] = "pass" if difference == 0 else "review_required"

    accessions = {
        record.get("source_accession")
        for record in metrics.values()
    }

    accessions.discard(None)

    provenance_status = (
        "consistent"
        if len(accessions) == 1
        and len(metrics) > 0
        and all(record.get("source_accession") for record in metrics.values())
        else "review_required"
    )

    all_passed = (
        all(status == "pass" for status in results.values())
        and provenance_status == "consistent"
    )

    return {
        "period_end": statement.get("period_end"),
        "status": "validated" if all_passed else "review_required",
        "checks": results,
        "differences": differences,
        "provenance_status": provenance_status,
        "source_accessions": sorted(accessions),
    }
