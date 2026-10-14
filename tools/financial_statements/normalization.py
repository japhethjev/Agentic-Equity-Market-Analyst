"""Normalize SEC financial observations into period-oriented statements."""

from decimal import Decimal


def normalize_balance_sheet(extracted: dict) -> list[dict]:
    """Convert balance-sheet metric observations into reporting periods."""
    periods = {}

    for metric, result in extracted.items():
        for observation in result.get("observations", []):
            period_end = observation["end"]

            statement = periods.setdefault(period_end, {
                "period_end": period_end,
                "period_type": "instant",
                "metrics": {},
            })

            if metric in statement["metrics"]:
                raise ValueError(
                    f"Duplicate observation: {metric} at {period_end}"
                )

            statement["metrics"][metric] = {
                "value": Decimal(str(observation["val"])),
                "unit": "USD",
                "source_accessions": [observation["accn"]],
                "source_filed": observation["filed"],
                "source_form": observation["form"],
                "concept": result.get("concept"),
            }

    return sorted(
        periods.values(),
        key=lambda statement: statement["period_end"],
        reverse=True,
    )


def normalize_quarterly_cash_flow(extracted: dict) -> list[dict]:
    """Convert reconstructed quarterly cash flows into period-oriented records."""
    periods = {}

    for metric, result in extracted.items():
        for observation in result.get("quarterly_observations", []):
            period_end = observation["end"]

            statement = periods.setdefault(period_end, {
                "period_end": period_end,
                "period_type": "quarterly",
                "metrics": {},
            })

            if metric in statement["metrics"]:
                raise ValueError(
                    f"Duplicate observation: {metric} at {period_end}"
                )

            statement["metrics"][metric] = {
                "value": Decimal(str(observation["val"])),
                "unit": "USD",
                "period_start": observation.get("start"),
                "calculation": observation.get("calculation"),
                "derived": observation.get("derived", False),
                "source_accessions": observation.get("source_accessions", []),
                "source_filed": observation.get("source_filed"),
                "concept": result.get("concept"),
            }

    anchor_dates = {
        observation["end"]
        for observation in extracted.get("operating_cash_flow", {}).get(
            "quarterly_observations", []
        )
    }

    return sorted(
        (
            statement
            for period_end, statement in periods.items()
            if period_end in anchor_dates
        ),
        key=lambda statement: statement["period_end"],
        reverse=True,
    )
