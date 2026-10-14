"""Build annual income statements from SEC company facts."""

from datetime import date
from decimal import Decimal, InvalidOperation

from tools.financial_statements.income_statement import (
    extract_income_statement_concepts,
)


def select_annual_income_observations(observations: list[dict]) -> list[dict]:
    """Select the latest filed observation for each fiscal year-end."""

    selected = {}

    for item in observations:
        if item.get("form") not in {"10-K", "10-K/A"}:
            continue

        try:
            start = date.fromisoformat(item["start"])
            end = date.fromisoformat(item["end"])
            filed = date.fromisoformat(item["filed"])
            value = Decimal(str(item["val"]))
        except (KeyError, TypeError, ValueError, InvalidOperation):
            continue

        duration = (end - start).days + 1

        if not 350 <= duration <= 380:
            continue

        if not value.is_finite() or not item.get("accn"):
            continue

        key = end.isoformat()
        existing = selected.get(key)

        if existing is None or (
            filed.isoformat(), item["accn"]
        ) > (
            existing["filed"], existing["accn"]
        ):
            selected[key] = item

    return sorted(
        selected.values(),
        key=lambda item: item["end"],
        reverse=True,
    )


def build_annual_income_statements(
    company_facts: dict,
    years: int = 5,
) -> list[dict]:
    """Return annual income statements with SEC provenance."""

    if isinstance(years, bool) or not isinstance(years, int) or years < 1:
        raise ValueError("years must be a positive integer")

    concepts = extract_income_statement_concepts(company_facts)
    periods = {}

    for metric, details in concepts.items():
        observations = select_annual_income_observations(
            details["reported_observations"]
        )

        for item in observations:
            period_end = item["end"]

            statement = periods.setdefault(
                period_end,
                {
                    "period_end": period_end,
                    "period_type": "annual",
                    "metrics": {},
                },
            )

            statement["metrics"][metric] = {
                "value": Decimal(str(item["val"])),
                "unit": details["unit"],
                "concept": details["concept"],
                "source_accession": item["accn"],
                "source_filed": item["filed"],
                "period_start": item["start"],
            }

    return [
        periods[end]
        for end in sorted(periods, reverse=True)[:years]
    ]
