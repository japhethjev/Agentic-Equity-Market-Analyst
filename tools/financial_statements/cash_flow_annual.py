"""Normalise SEC-reported annual cash-flow observations."""

from datetime import date
from decimal import Decimal, InvalidOperation


def normalize_annual_cash_flow(extracted: dict) -> list[dict]:
    """Build annual statements from full-year SEC 10-K observations."""

    periods = {}

    for metric_name, result in extracted.items():
        concept = result.get("concept")

        for obs in result.get("reported_observations", []):
            if obs.get("form") not in ("10-K", "10-K/A"):
                continue

            if obs.get("fp") != "FY":
                continue

            start = obs.get("start")
            end = obs.get("end")
            raw_value = obs.get("val")

            if not start or not end or raw_value is None:
                continue

            try:
                duration = (
                    date.fromisoformat(end)
                    - date.fromisoformat(start)
                ).days
                value = Decimal(str(raw_value))
            except (ValueError, TypeError, InvalidOperation):
                continue

            if not 330 <= duration <= 380 or not value.is_finite():
                continue

            candidate = {
                "value": value,
                "unit": "USD",
                "period_start": start,
                "period_end": end,
                "calculation": "SEC_REPORTED",
                "derived": False,
                "source_accession": obs.get("accn"),
                "source_filed": obs.get("filed"),
                "source_form": obs.get("form"),
                "concept": concept,
            }

            statement = periods.setdefault(
                end,
                {
                    "period_end": end,
                    "period_type": "annual",
                    "metrics": {},
                },
            )

            existing = statement["metrics"].get(metric_name)

            candidate_rank = (
                obs.get("filed") or "",
                obs.get("accn") or "",
            )

            existing_rank = (
                existing.get("source_filed") or "",
                existing.get("source_accession") or "",
            ) if existing else ("", "")

            if existing is None or candidate_rank > existing_rank:
                statement["metrics"][metric_name] = candidate

    return sorted(
        (
            statement
            for statement in periods.values()
            if "operating_cash_flow" in statement["metrics"]
        ),
        key=lambda statement: statement["period_end"],
        reverse=True,
    )
