"""Validate quarterly EPS and weighted-average share metrics."""

from decimal import Decimal, InvalidOperation

from tools.financial_statements.eps_reconstruction import (
    reconstruct_quarterly_eps,
)


PER_SHARE_METRICS = (
    "basic_eps",
    "diluted_eps",
    "basic_weighted_average_shares",
    "diluted_weighted_average_shares",
)


def validate_quarterly_per_share(statement: dict) -> dict:
    """Validate quarterly EPS and weighted-average shares."""

    metrics = statement.get("metrics", {})
    checks = {}

    checks["completeness"] = (
        "pass"
        if all(name in metrics for name in PER_SHARE_METRICS)
        else "missing_data"
    )

    if checks["completeness"] != "pass":
        return {
            "period_end": statement.get("period_end"),
            "status": "review_required",
            "checks": checks,
        }

    try:
        basic = Decimal(
            str(metrics["basic_weighted_average_shares"]["value"])
        )
        diluted = Decimal(
            str(metrics["diluted_weighted_average_shares"]["value"])
        )

        if not basic.is_finite() or not diluted.is_finite():
            raise InvalidOperation

        checks["positive_shares"] = (
            "pass" if basic > 0 and diluted > 0
            else "review_required"
        )

        checks["diluted_shares"] = (
            "pass" if diluted >= basic
            else "review_required"
        )

    except (KeyError, TypeError, ValueError, InvalidOperation):
        checks["positive_shares"] = "review_required"
        checks["diluted_shares"] = "review_required"

    for eps_name, share_name in (
        ("basic_eps", "basic_weighted_average_shares"),
        ("diluted_eps", "diluted_weighted_average_shares"),
    ):
        record = metrics[eps_name]

        if not record.get("derived", False):
            checks[eps_name] = "reported"
            continue

        try:
            income = Decimal(str(metrics["net_income"]["value"]))
            shares = Decimal(str(metrics[share_name]["value"]))

            if eps_name == "diluted_eps" and income < 0:
                shares = basic

            expected = reconstruct_quarterly_eps(income, shares)
            actual = Decimal(str(record["value"]))

            checks[eps_name] = (
                "pass"
                if actual.is_finite()
                and abs(actual - expected) < Decimal("0.000001")
                else "review_required"
            )

        except (
            KeyError, TypeError, ValueError,
            InvalidOperation, ZeroDivisionError,
        ):
            checks[eps_name] = "review_required"

    source_valid = True

    for name in PER_SHARE_METRICS:
        record = metrics[name]
        accessions = record.get("source_accessions")
        filed = record.get("source_filed")

        if (
            not isinstance(accessions, list)
            or not isinstance(filed, list)
            or not accessions
            or len(accessions) != len(filed)
            or any(not value for value in accessions + filed)
        ):
            source_valid = False

    checks["provenance"] = (
        "pass" if source_valid else "review_required"
    )

    valid = all(
        result in {"pass", "reported"}
        for result in checks.values()
    )

    return {
        "period_end": statement.get("period_end"),
        "status": "validated" if valid else "review_required",
        "checks": checks,
    }
