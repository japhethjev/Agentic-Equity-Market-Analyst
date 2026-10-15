"""Operating cash flow liquidity ratio with period-aligned liabilities."""

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation


def _decimal(value):
    if value is None:
        return None
    try:
        result = Decimal(str(value))
        return result if result.is_finite() else None
    except (ValueError, TypeError, InvalidOperation):
        return None


def calculate_operating_cash_flow_ratio(
    cash_flow: dict,
    balance_sheets: list[dict],
) -> dict:
    """Calculate OCF coverage using period-aligned current liabilities."""

    period_end = cash_flow.get("period_end")
    period_type = cash_flow.get("period_type")
    metric = cash_flow.get("metrics", {}).get("operating_cash_flow", {})

    result = {
        "period_end": period_end,
        "period_type": period_type,
        "value": None,
        "unit": "times",
        "status": "insufficient_data",
        "denominator_method": None,
        "annualized": period_type == "quarterly",
        "source_metrics": (
            "operating_cash_flow",
            "current_liabilities",
        ),
    }

    if period_type not in ("annual", "quarterly", "ttm"):
        return result

    ocf = _decimal(
        metric.get("ttm") if period_type == "ttm"
        else metric.get("value")
    )

    if ocf is None or not period_end:
        return result

    if period_type == "ttm" and metric.get("status") != "available":
        return result

    by_date = {
        sheet["period_end"]: _decimal(
            sheet.get("metrics", {})
            .get("current_liabilities", {})
            .get("value")
        )
        for sheet in balance_sheets
        if sheet.get("period_end")
    }

    closing = by_date.get(period_end)

    if closing is None:
        return result

    if closing <= 0:
        result["status"] = "not_meaningful"
        return result

    start = metric.get("period_start")

    if period_type == "ttm":
        quarters = metric.get("quarters_used", [])
        if len(quarters) != 4:
            return result

        oldest_quarter_end = min(quarters)

        quarter_records = {
            record["period_end"]: record
            for record in cash_flow.get("underlying_quarters", [])
        }

        oldest = quarter_records.get(oldest_quarter_end, {})
        start = (
            oldest.get("metrics", {})
            .get("operating_cash_flow", {})
            .get("period_start")
        )

    opening = None

    if start:
        target = date.fromisoformat(start) - timedelta(days=1)

        candidates = [
            (abs((date.fromisoformat(d) - target).days), d, v)
            for d, v in by_date.items()
            if v is not None
            and date.fromisoformat(d) < date.fromisoformat(start)
        ]

        if candidates:
            distance, _, value = min(candidates)
            if distance <= 14 and value > 0:
                opening = value

    if opening is not None:
        denominator = (opening + closing) / Decimal("2")
        result["denominator_method"] = "average_balance"
    else:
        denominator = closing
        result["denominator_method"] = "closing_balance"

    numerator = ocf * 4 if period_type == "quarterly" else ocf

    result["value"] = numerator / denominator
    result["status"] = "available"

    return result
