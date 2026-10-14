"""Extract standalone quarterly EPS and weighted-average shares."""

from decimal import Decimal

from tools.financial_statements.income_statement import (
    extract_income_statement_concepts,
)
from tools.financial_statements.period_selector import (
    select_quarterly_observations,
)


PER_SHARE_METRICS = (
    "basic_eps",
    "diluted_eps",
    "basic_weighted_average_shares",
    "diluted_weighted_average_shares",
)


def extract_reported_quarterly_per_share(
    company_facts: dict,
) -> dict:
    """Return directly reported quarterly EPS and share observations."""

    concepts = extract_income_statement_concepts(company_facts)
    periods = {}

    for metric in PER_SHARE_METRICS:
        details = concepts[metric]

        observations = select_quarterly_observations(
            details["reported_observations"]
        )

        for item in observations:
            end = item["end"]

            statement = periods.setdefault(end, {})

            statement[metric] = {
                "value": Decimal(str(item["val"])),
                "unit": details["unit"],
                "concept": details["concept"],
                "period_start": item["start"],
                "derived": False,
                "calculation": "AS_REPORTED",
                "source_accessions": [item["accn"]],
                "source_filed": [item["filed"]],
            }

    return periods
