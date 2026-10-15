"""Prepare investor-ready profitability ratio matrices."""

from decimal import Decimal

RATIO_LABELS = {
    "gross_profit_margin": "Gross Profit Margin",
    "operating_profit_margin": "Operating Profit Margin",
    "net_profit_margin": "Net Profit Margin",
    "return_on_assets": "Return on Assets (ROA)",
    "return_on_equity": "Return on Equity (ROE)",
}


def prepare_profitability_tables(profitability: dict) -> dict:
    """Create matrices with newest reporting periods as columns."""
    tables = {}

    for period_type in ("annual", "quarterly", "ttm"):
        observations = sorted(
            profitability.get(period_type, []),
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
                    values.append(f"{Decimal(str(value)):.2f}%")

            rows.append({
                "metric": metric,
                "label": label,
                "values": values,
            })

        tables[period_type] = {
            "period_type": period_type,
            "columns": ["Profitability Ratio", *periods],
            "rows": rows,
        }

    return tables
