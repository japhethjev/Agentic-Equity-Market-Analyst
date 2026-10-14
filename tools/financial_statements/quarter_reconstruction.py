"""Reconstruct standalone fourth-quarter financial observations."""

from datetime import date

from tools.financial_statements.period_selector import (
    select_annual_observations,
)


def reconstruct_fourth_quarters(
    observations: list[dict],
) -> list[dict]:
    """Derive Q4 as full-year less nine-month cumulative values."""

    annual = select_annual_observations(observations)
    reconstructed = []

    for full_year in annual:
        fy_start = full_year["start"]
        fy_end = date.fromisoformat(full_year["end"])

        candidates = []

        for item in observations:
            if item.get("form") not in {"10-Q", "10-Q/A"}:
                continue

            if item.get("start") != fy_start:
                continue

            try:
                nine_month_end = date.fromisoformat(item["end"])
                start_date = date.fromisoformat(item["start"])
            except (KeyError, TypeError, ValueError):
                continue

            duration = (nine_month_end - start_date).days + 1
            remaining = (fy_end - nine_month_end).days

            if not 260 <= duration <= 290:
                continue

            if not 80 <= remaining <= 100:
                continue

            # Use the filing vintage available when the annual
            # report was filed. Exclude later comparative filings.
            if item.get("filed", "") > full_year["filed"]:
                continue

            if (
                isinstance(item.get("val"), bool)
                or not isinstance(item.get("val"), (int, float))
                or not item.get("filed")
                or not item.get("accn")
            ):
                continue

            candidates.append(item)

        if not candidates:
            continue

        nine_month = max(
            candidates,
            key=lambda item: (item["filed"], item["accn"]),
        )

        reconstructed.append({
            "start": date.fromordinal(
                date.fromisoformat(nine_month["end"]).toordinal() + 1
            ).isoformat(),
            "end": full_year["end"],
            "val": full_year["val"] - nine_month["val"],
            "form": "DERIVED",
            "calculation": "FY_MINUS_9M",
            "derived": True,
            "fy_accn": full_year["accn"],
            "nine_month_accn": nine_month["accn"],
            "fy_filed": full_year["filed"],
            "nine_month_filed": nine_month["filed"],
        })

    return sorted(
        reconstructed,
        key=lambda item: item["end"],
        reverse=True,
    )
