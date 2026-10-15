"""Validation of historical liquidity analysis."""

from decimal import Decimal, InvalidOperation

RATIOS = (
    "current_ratio",
    "quick_ratio",
    "cash_ratio",
    "operating_cash_flow_ratio",
)

VALID_STATUSES = {
    "available",
    "insufficient_data",
    "not_meaningful",
}


def validate_liquidity_history(liquidity: dict) -> dict:
    """Validate liquidity observations and report data gaps."""
    errors = []
    gaps = []
    checked = 0

    for period_type in ("annual", "quarterly", "ttm"):
        observations = liquidity.get(period_type, [])
        dates = [item["period_end"] for item in observations]

        if dates != sorted(dates, reverse=True):
            errors.append(f"{period_type}: incorrect period ordering")

        if len(dates) != len(set(dates)):
            errors.append(f"{period_type}: duplicate reporting periods")

        for observation in observations:
            period_end = observation["period_end"]

            if observation.get("period_type") != period_type:
                errors.append(
                    f"{period_type} {period_end}: period type mismatch"
                )

            metrics = observation.get("metrics", {})

            for ratio in RATIOS:
                checked += 1
                result = metrics.get(ratio)

                if not isinstance(result, dict):
                    errors.append(
                        f"{period_type} {period_end}: missing {ratio}"
                    )
                    continue

                status = result.get("status")
                value = result.get("value")

                if status not in VALID_STATUSES:
                    errors.append(
                        f"{period_type} {period_end}: invalid status for {ratio}"
                    )
                    continue

                if status == "available":
                    try:
                        valid = (
                            value is not None
                            and Decimal(str(value)).is_finite()
                        )
                    except (ValueError, TypeError, InvalidOperation):
                        valid = False

                    if not valid:
                        errors.append(
                            f"{period_type} {period_end}: invalid value for {ratio}"
                        )

                    if ratio == "operating_cash_flow_ratio":
                        if result.get("denominator_method") not in {
                            "average_balance",
                            "closing_balance",
                        }:
                            errors.append(
                                f"{period_type} {period_end}: "
                                "invalid OCF denominator method"
                            )

                        expected_annualized = period_type == "quarterly"
                        if result.get("annualized") is not expected_annualized:
                            errors.append(
                                f"{period_type} {period_end}: "
                                "incorrect OCF annualization"
                            )

                elif value is not None:
                    errors.append(
                        f"{period_type} {period_end}: unexpected value for {ratio}"
                    )
                else:
                    gaps.append({
                        "period_type": period_type,
                        "period_end": period_end,
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
