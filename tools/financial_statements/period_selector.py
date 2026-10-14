"""Select annual financial observations from SEC Company Facts."""

from datetime import date


def select_annual_observations(
    observations: list[dict],
) -> list[dict]:
    """Select annual duration facts, deduplicated by reporting period."""

    selected = {}

    for item in observations:
        if item.get("form") not in {"10-K", "10-K/A"}:
            continue

        start = item.get("start")
        end = item.get("end")

        # Duration-based metrics require both dates.
        # Balance-sheet instant facts are handled separately.
        if not start or not end:
            continue

        try:
            start_date = date.fromisoformat(start)
            end_date = date.fromisoformat(end)
        except (TypeError, ValueError):
            continue

        duration = (end_date - start_date).days + 1

        # Accommodate 52- and 53-week fiscal years.
        if not 350 <= duration <= 380:
            continue

        if not isinstance(item.get("val"), (int, float)):
            continue

        if not item.get("filed") or not item.get("accn"):
            continue

        key = (start, end)

        existing = selected.get(key)

        if existing is None or (
            item["filed"], item["accn"]
        ) > (
            existing["filed"], existing["accn"]
        ):
            selected[key] = item

    return sorted(
        selected.values(),
        key=lambda item: item["end"],
        reverse=True,
    )


def select_quarterly_observations(
    observations: list[dict],
) -> list[dict]:
    """Select standalone quarterly duration observations.

    This selects approximately three-month income statement
    observations. It does not derive Q4 or convert cumulative
    year-to-date cash flow observations.
    """

    selected = {}

    for item in observations:
        if item.get("form") not in {
            "10-Q", "10-Q/A", "10-K", "10-K/A"
        }:
            continue

        start = item.get("start")
        end = item.get("end")

        if not start or not end:
            continue

        try:
            start_date = date.fromisoformat(start)
            end_date = date.fromisoformat(end)
        except (TypeError, ValueError):
            continue

        duration = (end_date - start_date).days + 1

        # Allow variation in fiscal-quarter lengths.
        if not 80 <= duration <= 100:
            continue

        value = item.get("val")

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
        ):
            continue

        if not item.get("filed") or not item.get("accn"):
            continue

        key = (start, end)

        existing = selected.get(key)

        if existing is None or (
            item["filed"], item["accn"]
        ) > (
            existing["filed"], existing["accn"]
        ):
            selected[key] = item

    return sorted(
        selected.values(),
        key=lambda item: item["end"],
        reverse=True,
    )


def select_rolling_financial_periods(
    observations: list[dict],
    period_type: str,
    years: int = 5,
    quarters: int = 12,
) -> list[dict]:
    """Return the latest available annual or quarterly observations.

    The window moves automatically as new SEC filings become
    available. No reporting year is hardcoded.
    """

    if period_type == "annual":
        if years < 1:
            raise ValueError("years must be positive")

        selected = select_annual_observations(observations)
        return selected[:years]

    if period_type == "quarterly":
        if quarters < 1:
            raise ValueError("quarters must be positive")

        selected = select_quarterly_observations(observations)
        return selected[:quarters]

    raise ValueError(
        "period_type must be 'annual' or 'quarterly'"
    )
