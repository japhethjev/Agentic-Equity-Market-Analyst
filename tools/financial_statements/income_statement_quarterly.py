"""Build standardised standalone quarterly income statements."""

from decimal import Decimal

from tools.financial_statements.income_statement import (
    extract_income_statement_concepts,
)
from tools.financial_statements.quarterly_dataset import (
    build_rolling_quarterly_dataset,
)


from tools.financial_statements.quarterly_per_share import (
    extract_reported_quarterly_per_share,
)
from tools.financial_statements.quarterly_share_dataset import (
    reconstruct_q4_share_observations,
)
from tools.financial_statements.eps_reconstruction import (
    reconstruct_quarterly_eps,
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

    # Add directly reported quarterly EPS and share counts.
    reported = extract_reported_quarterly_per_share(company_facts)

    for end, metrics in reported.items():
        if end in periods:
            periods[end]["metrics"].update(metrics)

    # Reconstruct Q4 share counts from annual and nine-month facts.
    share_metrics = (
        "basic_weighted_average_shares",
        "diluted_weighted_average_shares",
    )

    for metric in share_metrics:
        details = concepts[metric]
        reconstructed = reconstruct_q4_share_observations(
            details["reported_observations"]
        )

        for item in reconstructed:
            end = item["end"]

            if end not in periods:
                continue

            periods[end]["metrics"][metric] = {
                "value": Decimal(str(item["val"])),
                "unit": details["unit"],
                "concept": details["concept"],
                "period_start": item["start"],
                "derived": True,
                "calculation": item["calculation"],
                "source_accessions": [
                    item["fy_accn"],
                    item["nine_month_accn"],
                ],
                "source_filed": [
                    item["fy_filed"],
                    item["nine_month_filed"],
                ],
            }

    # Calculate Q4 EPS using net income and reconstructed shares.
    for statement in periods.values():
        metrics = statement["metrics"]

        for eps_metric, shares_metric in (
            ("basic_eps", "basic_weighted_average_shares"),
            ("diluted_eps", "diluted_weighted_average_shares"),
        ):
            shares = metrics.get(shares_metric)
            income = metrics.get("net_income")

            if not shares or not income:
                continue

            if not shares["derived"]:
                continue

            # Preserve any directly reported EPS.
            if eps_metric in metrics:
                continue

            # Diluted EPS must not be calculated using dilutive
            # shares when doing so would be anti-dilutive.
            denominator = shares["value"]

            if eps_metric == "diluted_eps" and income["value"] < 0:
                basic = metrics.get("basic_weighted_average_shares")
                if basic:
                    denominator = basic["value"]

            eps = reconstruct_quarterly_eps(
                income["value"],
                denominator,
            )

            metrics[eps_metric] = {
                "value": eps,
                "unit": concepts[eps_metric]["unit"],
                "concept": concepts[eps_metric]["concept"],
                "period_start": shares["period_start"],
                "derived": True,
                "calculation": "NET_INCOME_DIVIDED_BY_WEIGHTED_SHARES",
                "source_accessions": list(dict.fromkeys(
                    income["source_accessions"]
                    + shares["source_accessions"]
                )),
                "source_filed": list(dict.fromkeys(
                    income["source_filed"]
                    + shares["source_filed"]
                )),
            }

    return [
        periods[end]
        for end in sorted(periods, reverse=True)[:quarters]
    ]
