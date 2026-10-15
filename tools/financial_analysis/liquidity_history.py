"""Historical liquidity ratios across reporting frequencies."""

from tools.financial_analysis.liquidity import (
    calculate_liquidity_ratios,
)
from tools.financial_analysis.liquidity_cash_flow import (
    calculate_operating_cash_flow_ratio,
)


def build_liquidity_history(
    cash_flows: list[dict],
    balance_sheets: list[dict],
    period_type: str,
    quarterly_cash_flows: list[dict] | None = None,
) -> list[dict]:
    """Build liquidity observations, newest reporting date first."""
    if period_type not in {"annual", "quarterly", "ttm"}:
        raise ValueError("Unsupported reporting period")

    by_date = {
        sheet["period_end"]: sheet
        for sheet in balance_sheets
    }

    results = []

    for cash_flow in sorted(
        cash_flows,
        key=lambda item: item["period_end"],
        reverse=True,
    ):
        period_end = cash_flow["period_end"]
        sheet = by_date.get(period_end)

        if sheet is None:
            continue

        ratios = calculate_liquidity_ratios(sheet)

        record = dict(cash_flow)

        if period_type == "ttm":
            record["underlying_quarters"] = (
                quarterly_cash_flows or []
            )

        ocf_ratio = calculate_operating_cash_flow_ratio(
            record,
            balance_sheets,
        )

        results.append({
            "period_end": period_end,
            "period_type": period_type,
            "metrics": {
                **ratios,
                "operating_cash_flow_ratio": ocf_ratio,
            },
        })

    return results
