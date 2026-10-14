"""Reconstruct Q4 weighted-average shares from fiscal-year and nine-month data."""

from datetime import date
from decimal import Decimal


def reconstruct_q4_weighted_shares(
    annual_shares,
    nine_month_shares,
    fiscal_start,
    nine_month_end,
    fiscal_end,
):
    """Return Q4 weighted-average shares using actual reporting-period days."""

    start = date.fromisoformat(fiscal_start)
    nine_end = date.fromisoformat(nine_month_end)
    year_end = date.fromisoformat(fiscal_end)

    if not start <= nine_end < year_end:
        raise ValueError("Invalid fiscal reporting period dates")

    annual_days = (year_end - start).days + 1
    nine_month_days = (nine_end - start).days + 1
    q4_days = (year_end - nine_end).days

    if not 350 <= annual_days <= 380:
        raise ValueError("Annual period must contain approximately 52 or 53 weeks")

    if not 260 <= nine_month_days <= 295:
        raise ValueError("Nine-month period duration is invalid")

    if not 80 <= q4_days <= 100:
        raise ValueError("Q4 period duration is invalid")

    annual = Decimal(str(annual_shares))
    nine_month = Decimal(str(nine_month_shares))

    if annual <= 0 or nine_month <= 0:
        raise ValueError("Weighted-average shares must be positive")

    result = (
        annual * Decimal(annual_days)
        - nine_month * Decimal(nine_month_days)
    ) / Decimal(q4_days)

    if result <= 0:
        raise ValueError("Reconstructed Q4 shares must be positive")

    return result
