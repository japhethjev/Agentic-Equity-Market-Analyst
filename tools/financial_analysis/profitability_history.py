"""Historical profitability calculations across reporting frequencies."""

from tools.financial_analysis.profitability import (
    calculate_profitability_ratios,
    calculate_period_return_ratios,
)


def build_profitability_history(
    income_statements: list[dict],
    balance_sheets: list[dict],
    period_type: str,
) -> list[dict]:
    """Return profitability observations, newest reporting period first."""
    if period_type not in {"annual", "quarterly", "ttm"}:
        raise ValueError("Unsupported reporting period")

    results = []

    for statement in sorted(
        income_statements,
        key=lambda item: item["period_end"],
        reverse=True,
    ):
        margins = calculate_profitability_ratios(statement)

        try:
            returns = calculate_period_return_ratios(
                statement,
                balance_sheets,
                period_type,
            )
        except (KeyError, TypeError, ValueError) as exc:
            if not (
                isinstance(exc, ValueError)
                and str(exc) == "Actual reporting period start is required"
            ):
                raise

            returns = {
                name: {
                    "value": None,
                    "status": "insufficient_data",
                    "unit": "percent",
                    "period_type": period_type,
                    "period_end": statement["period_end"],
                    "opening_balance_date": None,
                    "closing_balance_date": statement["period_end"],
                    "annualization_factor": None,
                    "source_metrics": ("net_income", metric),
                }
                for name, metric in (
                    ("return_on_assets", "total_assets"),
                    ("return_on_equity", "shareholders_equity"),
                )
            }

        results.append({
            "period_end": statement["period_end"],
            "period_type": period_type,
            "metrics": {**margins, **returns},
        })

    return results
