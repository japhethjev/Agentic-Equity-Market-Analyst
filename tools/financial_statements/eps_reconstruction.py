"""Calculate estimated quarterly EPS from net income and weighted shares."""

from decimal import Decimal, InvalidOperation


def reconstruct_quarterly_eps(
    net_income,
    weighted_average_shares,
):
    """Return unrounded EPS as Decimal."""

    try:
        income = Decimal(str(net_income))
        shares = Decimal(str(weighted_average_shares))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Invalid EPS calculation inputs") from None

    if not income.is_finite() or not shares.is_finite():
        raise ValueError("EPS inputs must be finite")

    if shares <= 0:
        raise ValueError("Weighted-average shares must be positive")

    return income / shares
