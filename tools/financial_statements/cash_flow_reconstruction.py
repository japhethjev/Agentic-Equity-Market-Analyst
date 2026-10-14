"""Reconstruct standalone quarterly cash flows from SEC cumulative facts."""

from datetime import date
from decimal import Decimal, InvalidOperation


def reconstruct_quarterly_cash_flows(
    observations: list[dict],
) -> list[dict]:
    """Convert cumulative SEC cash-flow observations into quarters."""

    grouped = {}

    for item in observations:
        if item.get("form") not in {
            "10-Q", "10-Q/A", "10-K", "10-K/A"
        }:
            continue

        try:
            start = date.fromisoformat(item["start"])
            end = date.fromisoformat(item["end"])
            filed = date.fromisoformat(item["filed"])
            value = Decimal(str(item["val"]))
        except (
            KeyError, TypeError, ValueError, InvalidOperation
        ):
            continue

        if (
            end < start
            or not value.is_finite()
            or isinstance(item["val"], bool)
            or not item.get("accn")
        ):
            continue

        duration = (end - start).days + 1

        if 80 <= duration <= 105:
            quarter = 1
        elif 170 <= duration <= 200:
            quarter = 2
        elif 260 <= duration <= 295:
            quarter = 3
        elif 350 <= duration <= 380:
            quarter = 4
        else:
            continue

        # Group by actual fiscal-year start, not SEC fy metadata.
        key = start.isoformat()
        bucket = grouped.setdefault(key, {})

        existing = bucket.get(quarter)

        if existing is None or (
            filed.isoformat(), item["accn"]
        ) > (
            existing["filed"], existing["accn"]
        ):
            bucket[quarter] = item

    result = []

    for fiscal_start, periods in grouped.items():
        previous = None

        for quarter in (1, 2, 3, 4):
            current = periods.get(quarter)

            if current is None:
                break

            if quarter == 1:
                quarterly_value = Decimal(str(current["val"]))
                quarter_start = fiscal_start
                source_accessions = [current["accn"]]
            else:
                if previous is None:
                    break

                quarterly_value = (
                    Decimal(str(current["val"]))
                    - Decimal(str(previous["val"]))
                )

                quarter_start = date.fromordinal(
                    date.fromisoformat(
                        previous["end"]
                    ).toordinal() + 1
                ).isoformat()

                source_accessions = [
                    previous["accn"],
                    current["accn"],
                ]

            result.append({
                "start": quarter_start,
                "end": current["end"],
                "val": quarterly_value,
                "quarter": quarter,
                "fiscal_year_start": fiscal_start,
                "derived": quarter != 1,
                "source_accessions": source_accessions,
                "source_filed": current["filed"],
                "calculation": (
                    "AS_REPORTED"
                    if quarter == 1
                    else "CUMULATIVE_DIFFERENCE"
                ),
            })

            previous = current

    return sorted(
        result,
        key=lambda item: item["end"],
        reverse=True,
    )
