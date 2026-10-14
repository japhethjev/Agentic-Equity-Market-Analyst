"""Trailing-twelve-month cash-flow calculations."""

from decimal import Decimal, InvalidOperation

from tools.financial_statements.cash_flow_continuity import (
    continuous_cash_flow_quarters,
)


def calculate_cash_flow_ttm(
    cash_flow: dict,
    reporting_date: str,
) -> dict:
    """Calculate TTM cash flows using four consecutive aligned quarters."""

    result = {}

    for metric, details in cash_flow.items():
        observations = details.get("quarterly_observations", [])

        aligned = [
            item for item in observations
            if item.get("end", "") <= reporting_date
        ]

        quarters = continuous_cash_flow_quarters(aligned, limit=4)

        if (
            len(quarters) != 4
            or quarters[0]["end"] != reporting_date
        ):
            result[metric] = {
                "status": "insufficient_data",
                "ttm": None,
                "reporting_date": reporting_date,
            }
            continue

        try:
            values = [
                Decimal(str(item["val"]))
                for item in quarters
            ]

            if not all(value.is_finite() for value in values):
                raise ValueError("Non-finite financial value")

            ttm = sum(values, Decimal("0"))

        except (KeyError, TypeError, InvalidOperation, ValueError):
            result[metric] = {
                "status": "invalid_data",
                "ttm": None,
                "reporting_date": reporting_date,
            }
            continue

        result[metric] = {
            "status": "available",
            "ttm": ttm,
            "reporting_date": reporting_date,
            "quarters_used": [
                item["end"] for item in quarters
            ],
        }

    return result
