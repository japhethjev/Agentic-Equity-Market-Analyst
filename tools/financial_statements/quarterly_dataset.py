"""Build continuous quarterly financial datasets."""

from datetime import date, timedelta

from tools.financial_statements.period_selector import (
    select_quarterly_observations,
)
from tools.financial_statements.quarter_reconstruction import (
    reconstruct_fourth_quarters,
)


def build_rolling_quarterly_dataset(
    observations: list[dict],
    quarters: int = 12,
) -> list[dict]:
    """Return the latest consecutive standalone fiscal quarters."""

    if isinstance(quarters, bool) or not isinstance(quarters, int):
        raise ValueError("quarters must be a positive integer")

    if quarters < 1:
        raise ValueError("quarters must be a positive integer")

    reported = select_quarterly_observations(observations)
    derived = reconstruct_fourth_quarters(observations)

    combined = reported + derived

    # Deduplicate identical reporting periods.
    # Prefer directly reported values over reconstructed values.
    unique = {}

    for item in combined:
        key = (item["start"], item["end"])

        existing = unique.get(key)

        if existing is None or (
            existing.get("derived", False)
            and not item.get("derived", False)
        ):
            unique[key] = item

    ordered = sorted(
        unique.values(),
        key=lambda item: item["end"],
        reverse=True,
    )

    if not ordered:
        return []

    # Start with the latest available reporting quarter.
    continuous = [ordered[0]]

    for item in ordered[1:]:
        previous = continuous[-1]

        expected_end = (
            date.fromisoformat(previous["start"])
            - timedelta(days=1)
        )

        actual_end = date.fromisoformat(item["end"])

        if actual_end == expected_end:
            continuous.append(item)
        else:
            # Never silently skip a missing quarter.
            break

        if len(continuous) >= quarters:
            break

    return continuous[:quarters]
