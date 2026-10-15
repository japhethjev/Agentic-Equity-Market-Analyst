"""Validation of historical profitability analysis."""

RATIOS = (
    "gross_profit_margin",
    "operating_profit_margin",
    "net_profit_margin",
    "return_on_assets",
    "return_on_equity",
)

VALID_STATUSES = {
    "available",
    "insufficient_data",
    "not_meaningful",
}


def validate_profitability_history(profitability: dict) -> dict:
    """Validate profitability observations and report data gaps."""
    errors = []
    gaps = []
    checked = 0

    for period_type in ("annual", "quarterly", "ttm"):
        observations = profitability.get(period_type, [])

        dates = [item["period_end"] for item in observations]

        if dates != sorted(dates, reverse=True):
            errors.append(f"{period_type}: incorrect period ordering")

        if len(dates) != len(set(dates)):
            errors.append(f"{period_type}: duplicate reporting periods")

        for observation in observations:
            metrics = observation.get("metrics", {})

            for ratio in RATIOS:
                checked += 1
                result = metrics.get(ratio)

                if result is None:
                    errors.append(
                        f"{period_type} {observation['period_end']}: "
                        f"missing {ratio}"
                    )
                    continue

                status = result.get("status")
                value = result.get("value")

                if status not in VALID_STATUSES:
                    errors.append(
                        f"{period_type} {observation['period_end']}: "
                        f"invalid status for {ratio}"
                    )
                elif status == "available":
                    if value is None or not value.is_finite():
                        errors.append(
                            f"{period_type} {observation['period_end']}: "
                            f"invalid value for {ratio}"
                        )
                elif value is not None:
                    errors.append(
                        f"{period_type} {observation['period_end']}: "
                        f"unexpected value for {ratio}"
                    )
                else:
                    gaps.append({
                        "period_type": period_type,
                        "period_end": observation["period_end"],
                        "ratio": ratio,
                        "status": status,
                    })

    return {
        "status": (
            "failed" if errors else
            "validated_with_gaps" if gaps else
            "validated"
        ),
        "checks": checked,
        "errors": errors,
        "gaps": gaps,
    }
