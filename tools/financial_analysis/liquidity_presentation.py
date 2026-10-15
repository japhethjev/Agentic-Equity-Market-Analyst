"""Prepare investor-ready liquidity ratio matrices."""

from decimal import Decimal

RATIO_LABELS = {
    "current_ratio": "Current Ratio",
    "quick_ratio": "Quick Ratio",
    "cash_ratio": "Cash Ratio",
    "operating_cash_flow_ratio": "Operating Cash Flow Ratio",
}


def prepare_liquidity_tables(liquidity: dict) -> dict:
    """Create liquidity matrices with newest periods first."""
    tables = {}

    for period_type in ("annual", "quarterly", "ttm"):
        observations = sorted(
            liquidity.get(period_type, []),
            key=lambda item: item["period_end"],
            reverse=True,
        )

        periods = [item["period_end"] for item in observations]
        rows = []

        for metric, label in RATIO_LABELS.items():
            values = []

            for observation in observations:
                result = observation.get("metrics", {}).get(metric, {})
                value = result.get("value")

                if result.get("status") != "available" or value is None:
                    values.append("N/A")
                else:
                    values.append(f"{Decimal(str(value)):.2f}x")

            rows.append({
                "metric": metric,
                "label": label,
                "values": values,
            })

        tables[period_type] = {
            "period_type": period_type,
            "columns": ["Liquidity Ratio", *periods],
            "rows": rows,
        }

    return tables
