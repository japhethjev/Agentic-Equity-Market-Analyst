"""Build rolling TTM income statements from four consecutive quarters."""

from datetime import date, timedelta
from decimal import Decimal

from tools.financial_statements.income_statement_quarterly import (
    MONETARY_METRICS,
)
from tools.financial_statements.eps_reconstruction import (
    reconstruct_quarterly_eps,
)


def build_ttm_income_statements(
    quarterly_statements: list[dict],
) -> list[dict]:
    """Sum four consecutive quarterly income statements."""

    ordered = sorted(
        quarterly_statements,
        key=lambda statement: statement["period_end"],
        reverse=True,
    )

    results = []

    for index in range(len(ordered) - 3):
        window = ordered[index:index + 4]

        # Verify reporting-period continuity.
        continuous = True

        for newer, older in zip(window, window[1:]):
            newer_start = date.fromisoformat(
                newer["metrics"]["revenue"]["period_start"]
            )
            older_end = date.fromisoformat(older["period_end"])

            if older_end != newer_start - timedelta(days=1):
                continuous = False
                break

        if not continuous:
            continue

        metrics = {}

        for metric in MONETARY_METRICS:
            observations = [
                statement["metrics"][metric]
                for statement in window
            ]

            metrics[metric] = {
                "value": sum(
                    (Decimal(str(item["value"])) for item in observations),
                    Decimal("0"),
                ),
                "unit": observations[0]["unit"],
                "calculation": "SUM_FOUR_QUARTERS",
                "source_accessions": list(dict.fromkeys(
                    accession
                    for item in observations
                    for accession in item["source_accessions"]
                )),
            }

        # Duration-weighted shares across the four quarters.
        for share_metric in (
            "basic_weighted_average_shares",
            "diluted_weighted_average_shares",
        ):
            weighted_total = Decimal("0")
            total_days = 0
            sources = []

            for statement in window:
                observation = statement["metrics"][share_metric]
                start = date.fromisoformat(observation["period_start"])
                end = date.fromisoformat(statement["period_end"])
                days = (end - start).days + 1

                if days <= 0:
                    raise ValueError("Invalid quarterly share period")

                weighted_total += Decimal(str(observation["value"])) * days
                total_days += days
                sources.extend(observation["source_accessions"])

            metrics[share_metric] = {
                "value": weighted_total / Decimal(total_days),
                "unit": window[0]["metrics"][share_metric]["unit"],
                "calculation": "DURATION_WEIGHTED_FOUR_QUARTERS",
                "source_accessions": list(dict.fromkeys(sources)),
            }

        # Recalculate TTM EPS from TTM net income and shares.
        net_income = metrics["net_income"]["value"]

        for eps_metric, share_metric in (
            ("basic_eps", "basic_weighted_average_shares"),
            ("diluted_eps", "diluted_weighted_average_shares"),
        ):
            denominator = metrics[share_metric]["value"]

            if eps_metric == "diluted_eps" and net_income < 0:
                denominator = metrics["basic_weighted_average_shares"]["value"]

            metrics[eps_metric] = {
                "value": reconstruct_quarterly_eps(net_income, denominator),
                "unit": "USD/shares",
                "calculation": "TTM_NET_INCOME_DIVIDED_BY_WEIGHTED_SHARES",
                "source_accessions": list(dict.fromkeys(
                    metrics["net_income"]["source_accessions"]
                    + metrics[share_metric]["source_accessions"]
                )),
            }

        results.append({
            "period_start": window[-1]["metrics"]["revenue"]["period_start"],
            "period_end": window[0]["period_end"],
            "period_type": "TTM",
            "quarters_included": [
                statement["period_end"]
                for statement in window
            ],
            "metrics": metrics,
        })

    return results
