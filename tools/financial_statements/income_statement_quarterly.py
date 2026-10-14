"""Build standardised standalone quarterly income statements."""

from decimal import Decimal

from tools.financial_statements.income_statement import (
    extract_income_statement_concepts,
)
from tools.financial_statements.quarterly_dataset import (
    build_rolling_quarterly_dataset,
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


def build_quarterly_income_statements(
    company_facts: dict,
    quarters: int = 12,
) -> list[dict]:
    """Build quarterly monetary statements with SEC provenance."""

    if isinstance(quarters, bool) or not isinstance(quarters, int) or quarters < 1:
        raise ValueError("quarters must be a positive integer")

    concepts = extract_income_statement_concepts(company_facts)
    periods = {}

    for metric in MONETARY_METRICS:
        details = concepts[metric]

        observations = build_rolling_quarterly_dataset(
            details["reported_observations"],
            quarters=quarters,
        )

        for item in observations:
            end = item["end"]

            statement = periods.setdefault(
                end,
                {
                    "period_end": end,
                    "period_type": "quarterly",
                    "metrics": {},
                },
            )

            derived = item.get("derived", False)

            statement["metrics"][metric] = {
                "value": Decimal(str(item["val"])),
                "unit": details["unit"],
                "concept": details["concept"],
                "period_start": item["start"],
                "derived": derived,
                "calculation": item.get(
                    "calculation",
                    "AS_REPORTED",
                ),
                "source_accessions": (
                    [item["fy_accn"], item["nine_month_accn"]]
                    if derived
                    else [item["accn"]]
                ),
                "source_filed": (
                    [item["fy_filed"], item["nine_month_filed"]]
                    if derived
                    else [item["filed"]]
                ),
            }

    return [
        periods[end]
        for end in sorted(periods, reverse=True)[:quarters]
    ]
