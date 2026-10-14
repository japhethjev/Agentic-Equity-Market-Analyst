"""Align cash-flow metrics to a common reporting quarter."""


def align_cash_flow_metrics(cash_flow: dict) -> dict:
    """Return metrics aligned to the latest available quarter."""

    latest_dates = [
        records[0]["end"]
        for details in cash_flow.values()
        if (records := details.get("quarterly_observations", []))
    ]

    if not latest_dates:
        return {
            "reporting_date": None,
            "metrics": {},
        }

    reporting_date = max(latest_dates)
    aligned = {}

    for metric, details in cash_flow.items():
        records = details.get("quarterly_observations", [])

        matching = next(
            (
                item for item in records
                if item["end"] == reporting_date
            ),
            None,
        )

        aligned[metric] = {
            "status": (
                "aligned"
                if matching is not None
                else "unavailable_for_period"
            ),
            "observation": matching,
            "concept": details["concept"],
        }

    return {
        "reporting_date": reporting_date,
        "metrics": aligned,
    }
