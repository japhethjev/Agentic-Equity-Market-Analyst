from decimal import Decimal, InvalidOperation


LIQUIDITY_RATIOS = {
    "current_ratio": ("current_assets", "current_liabilities"),
    "quick_ratio": ("current_assets", "inventory", "current_liabilities"),
    "cash_ratio": ("cash_and_equivalents", "current_liabilities"),
}


def calculate_liquidity_ratios(balance_sheet: dict) -> dict:
    """Calculate point-in-time liquidity ratios from a balance sheet."""
    metrics = balance_sheet.get("metrics", {})
    period_end = balance_sheet.get("period_end")
    results = {}

    def get_value(name):
        raw = metrics.get(name, {}).get("value")
        if raw is None:
            return None
        try:
            value = Decimal(str(raw))
            return value if value.is_finite() else None
        except (InvalidOperation, ValueError, TypeError):
            return None

    liabilities = get_value("current_liabilities")

    for ratio_name, source_metrics in LIQUIDITY_RATIOS.items():
        result = {
            "period_end": period_end,
            "value": None,
            "unit": "times",
            "status": "insufficient_data",
            "source_metrics": source_metrics,
            "denominator_method": "closing_balance",
        }

        values = [get_value(name) for name in source_metrics]

        if all(value is not None for value in values):
            if liabilities is not None and liabilities > 0:
                if ratio_name == "quick_ratio":
                    numerator = values[0] - values[1]
                else:
                    numerator = values[0]

                if numerator >= 0:
                    result["value"] = numerator / liabilities
                    result["status"] = "available"
                else:
                    result["status"] = "not_meaningful"
            elif liabilities is not None:
                result["status"] = "not_meaningful"

        results[ratio_name] = result

    return results
