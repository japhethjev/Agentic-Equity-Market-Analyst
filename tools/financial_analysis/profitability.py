"""Profitability ratios calculated from validated financial statements."""

from decimal import Decimal, InvalidOperation


PROFITABILITY_RATIOS = {
    "gross_profit_margin": ("gross_profit", "revenue"),
    "operating_profit_margin": ("operating_income", "revenue"),
    "net_profit_margin": ("net_income", "revenue"),
}


def calculate_profitability_ratios(statement: dict) -> dict:
    """Calculate margins as percentages from raw financial values."""
    metrics = statement.get("metrics", {})
    period_end = statement.get("period_end")
    results = {}

    for ratio, (numerator, denominator) in PROFITABILITY_RATIOS.items():
        source_metrics = (numerator, denominator)

        try:
            top = Decimal(str(metrics[numerator]["value"]))
            bottom = Decimal(str(metrics[denominator]["value"]))

            if not top.is_finite() or not bottom.is_finite():
                raise ValueError("Non-finite financial value")

            if bottom <= 0:
                raise ValueError("Revenue must be positive")

            value = (top / bottom) * Decimal("100")
            status = "available"

        except (KeyError, TypeError, ValueError, InvalidOperation):
            value = None
            status = "insufficient_data"

        results[ratio] = {
            "value": value,
            "unit": "percent",
            "status": status,
            "period_end": period_end,
            "source_metrics": source_metrics,
        }

    return results


def calculate_return_ratios(
    ttm_statement: dict,
    balance_sheets: list[dict],
) -> dict:
    """Calculate ROA and ROE using exact TTM-aligned balance sheets."""
    from datetime import date, timedelta

    start = date.fromisoformat(ttm_statement["period_start"])
    end = ttm_statement["period_end"]
    opening_date = (start - timedelta(days=1)).isoformat()

    sheets = {
        statement["period_end"]: statement
        for statement in balance_sheets
    }

    results = {}

    for ratio, balance_metric in (
        ("return_on_assets", "total_assets"),
        ("return_on_equity", "shareholders_equity"),
    ):
        value = None
        status = "insufficient_data"
        method = None

        try:
            income = Decimal(
                str(ttm_statement["metrics"]["net_income"]["value"])
            )
            opening = Decimal(
                str(sheets[opening_date]["metrics"][balance_metric]["value"])
            )
            closing = Decimal(
                str(sheets[end]["metrics"][balance_metric]["value"])
            )

            average = (opening + closing) / Decimal("2")

            if all(
                number.is_finite()
                for number in (income, opening, closing, average)
            ) and average > 0:
                value = income / average * Decimal("100")
                status = "available"

        except (KeyError, TypeError, ValueError, InvalidOperation):
            pass

        results[ratio] = {
            "value": value,
            "unit": "percent",
            "status": status,
            "period_start": ttm_statement["period_start"],
            "period_end": end,
            "opening_balance_date": opening_date,
            "closing_balance_date": end,
            "source_metrics": ("net_income", balance_metric),
        }

    return results


def calculate_period_return_ratios(
    statement: dict,
    balance_sheets: list[dict],
    period_type: str,
) -> dict:
    """Calculate period-aligned annual, quarterly or TTM ROA and ROE."""
    from datetime import date, timedelta

    if period_type not in {"annual", "quarterly", "ttm"}:
        raise ValueError("Unsupported reporting period")

    end = date.fromisoformat(statement["period_end"])

    period_start = (
        statement.get("period_start")
        or statement.get("metrics", {}).get("net_income", {}).get("period_start")
    )
    if not period_start:
        raise ValueError("Actual reporting period start is required")

    start = date.fromisoformat(period_start)
    days = (end - start).days + 1

    if days <= 0:
        raise ValueError("Invalid reporting period")

    opening = start - timedelta(days=1)
    factor = (
        Decimal("365.25") / Decimal(days)
        if period_type == "quarterly"
        else Decimal("1")
    )

    sheets = {s["period_end"]: s["metrics"] for s in balance_sheets}
    results = {}

    for name, metric in (
        ("return_on_assets", "total_assets"),
        ("return_on_equity", "shareholders_equity"),
    ):
        value = None
        status = "insufficient_data"
        method = None

        try:
            income = Decimal(str(statement["metrics"]["net_income"]["value"]))
            last = Decimal(str(sheets[end.isoformat()][metric]["value"]))
            opening_metric = sheets.get(opening.isoformat(), {}).get(metric)
            first = (
                Decimal(str(opening_metric["value"]))
                if opening_metric is not None
                else None
            )
            denominator = (
                (first + last) / Decimal("2")
                if first is not None and first.is_finite()
                else last
            )
            method = (
                "average_balance"
                if first is not None and first.is_finite()
                else "closing_balance"
            )

            if income.is_finite() and denominator.is_finite():
                if denominator > 0:
                    value = income / denominator * factor * Decimal("100")
                    status = "available"
                elif denominator < 0:
                    status = "not_meaningful"

        except (KeyError, TypeError, ValueError, InvalidOperation):
            pass

        results[name] = {
            "value": value,
            "status": status,
            "unit": "percent",
            "period_type": period_type,
            "period_end": end.isoformat(),
            "opening_balance_date": opening.isoformat(),
            "closing_balance_date": end.isoformat(),
            "annualization_factor": factor,
            "denominator_method": method,
            "source_metrics": ("net_income", metric),
        }

    return results
