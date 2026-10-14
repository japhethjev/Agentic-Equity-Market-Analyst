"""Reconstruct Q4 weighted-average shares from SEC observations."""

from datetime import date, timedelta

from tools.financial_statements.period_selector import (
    select_annual_observations,
)
from tools.financial_statements.share_reconstruction import (
    reconstruct_q4_weighted_shares,
)


def reconstruct_q4_share_observations(observations):
    """Return Q4 shares with annual and nine-month filing provenance."""

    results = []

    # Select the earliest available annual filing for each
    # fiscal period, avoiding later comparative observations.
    annual_by_period = {}

    for item in observations:
        if item.get("form") not in {"10-K", "10-K/A"}:
            continue

        if not item.get("start") or not item.get("end"):
            continue

        if not item.get("filed") or not item.get("accn"):
            continue

        key = (item["start"], item["end"])
        existing = annual_by_period.get(key)

        if existing is None or (
            item["filed"], item["accn"]
        ) < (
            existing["filed"], existing["accn"]
        ):
            annual_by_period[key] = item

    original_annual = select_annual_observations(
        list(annual_by_period.values())
    )

    for annual in original_annual:
        fy_start = annual["start"]
        fy_end = date.fromisoformat(annual["end"])

        candidates = []

        for item in observations:
            if item.get("form") not in {"10-Q", "10-Q/A"}:
                continue

            if item.get("start") != fy_start:
                continue

            if not item.get("filed") or not item.get("accn"):
                continue

            if item["filed"] > annual["filed"]:
                continue

            try:
                nine_end = date.fromisoformat(item["end"])
                filed_date = date.fromisoformat(item["filed"])

                # Exclude comparative observations from later filings.
                filing_lag = (filed_date - nine_end).days
                if not 0 <= filing_lag <= 120:
                    continue
                duration = (
                    nine_end - date.fromisoformat(fy_start)
                ).days + 1
                q4_days = (fy_end - nine_end).days
            except (KeyError, TypeError, ValueError):
                continue

            if not 260 <= duration <= 295:
                continue

            if not 80 <= q4_days <= 100:
                continue

            candidates.append(item)

        if not candidates:
            continue

        nine_month = max(
            candidates,
            key=lambda item: (item["filed"], item["accn"]),
        )

        try:
            shares = reconstruct_q4_weighted_shares(
                annual["val"],
                nine_month["val"],
                fy_start,
                nine_month["end"],
                annual["end"],
            )
        except (ValueError, ArithmeticError, TypeError):
            continue

        results.append({
            "start": (
                date.fromisoformat(nine_month["end"])
                + timedelta(days=1)
            ).isoformat(),
            "end": annual["end"],
            "val": shares,
            "derived": True,
            "calculation": "DURATION_WEIGHTED_FY_MINUS_9M",
            "fy_accn": annual["accn"],
            "nine_month_accn": nine_month["accn"],
            "fy_filed": annual["filed"],
            "nine_month_filed": nine_month["filed"],
        })

    return sorted(
        results,
        key=lambda item: item["end"],
        reverse=True,
    )
