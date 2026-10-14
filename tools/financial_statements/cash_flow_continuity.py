"""Validate consecutive quarterly cash-flow observations."""

from datetime import date, timedelta


def continuous_cash_flow_quarters(
    observations: list[dict],
    limit: int = 12,
) -> list[dict]:
    """Return consecutive quarters starting with the latest."""

    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")

    if not observations:
        return []

    ordered = sorted(
        observations,
        key=lambda item: item["end"],
        reverse=True,
    )

    continuous = [ordered[0]]

    for item in ordered[1:]:
        previous = continuous[-1]

        expected_end = (
            date.fromisoformat(previous["start"])
            - timedelta(days=1)
        )

        actual_end = date.fromisoformat(item["end"])

        if actual_end != expected_end:
            break

        continuous.append(item)

        if len(continuous) >= limit:
            break

    return continuous[:limit]
