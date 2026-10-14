"""Standardized financial statement presentation."""

from decimal import Decimal

SHARE_METRICS = {
    "basic_weighted_average_shares",
    "diluted_weighted_average_shares",
}

EPS_METRICS = {"basic_eps", "diluted_eps"}


def format_financial_statement_table(
    statements: list[dict],
    metric_order: list[str],
) -> dict:
    """Return financial metrics as rows and reporting periods as columns."""

    ordered = sorted(
        statements,
        key=lambda item: item["period_end"],
        reverse=True,
    )

    periods = [item["period_end"] for item in ordered]
    rows = []

    for metric in metric_order:
        if metric in EPS_METRICS:
            unit, divisor, precision = "USD/share", Decimal(1), 2
        elif metric in SHARE_METRICS:
            unit, divisor, precision = "millions", Decimal(1_000_000), 2
        else:
            unit, divisor, precision = "USD millions", Decimal(1_000_000), 0

        values = []

        for statement in ordered:
            observation = statement.get("metrics", {}).get(metric)

            if observation is None or observation.get("value") is None:
                values.append(None)
                continue

            value = Decimal(str(observation["value"])) / divisor
            values.append(f"{value:,.{precision}f}")

        rows.append({
            "metric": metric,
            "unit": unit,
            "values": values,
        })

    return {
        "periods": periods,
        "rows": rows,
    }
