"""Validate balance-sheet consistency without inventing values."""

from decimal import Decimal


def validate_balance_sheet(balance_sheet: dict) -> dict:
    """Check accounting equation and debt representation."""

    def latest(metric):
        observations = balance_sheet.get(metric, {}).get(
            "observations", []
        )
        return observations[0] if observations else None

    assets = latest("total_assets")
    liabilities = latest("total_liabilities")
    equity = latest("shareholders_equity")

    result = {
        "accounting_equation": "unavailable",
        "reporting_dates_aligned": False,
        "filings_aligned": False,
        "debt_reconciliation": "unavailable",
        "debt_difference": None,
    }

    if all(item is not None for item in (assets, liabilities, equity)):
        result["reporting_dates_aligned"] = (
            len({item["end"] for item in (assets, liabilities, equity)}) == 1
        )
        result["filings_aligned"] = (
            len({item["accn"] for item in (assets, liabilities, equity)}) == 1
        )

        if result["reporting_dates_aligned"] and result["filings_aligned"]:
            difference = (
                Decimal(str(assets["val"]))
                - Decimal(str(liabilities["val"]))
                - Decimal(str(equity["val"]))
            )
            result["accounting_equation"] = (
                "pass" if difference == 0 else "fail"
            )

    total_debt = latest("long_term_debt")
    current_debt = latest("current_portion_long_term_debt")
    noncurrent_debt = latest("noncurrent_long_term_debt")

    if all(
        item is not None
        for item in (total_debt, current_debt, noncurrent_debt)
    ):
        if len({
            (item["end"], item["accn"])
            for item in (total_debt, current_debt, noncurrent_debt)
        }) == 1:
            difference = (
                Decimal(str(current_debt["val"]))
                + Decimal(str(noncurrent_debt["val"]))
                - Decimal(str(total_debt["val"]))
            )
            result["debt_difference"] = difference
            result["debt_reconciliation"] = (
                "pass" if difference == 0 else "review_required"
            )

    return result
