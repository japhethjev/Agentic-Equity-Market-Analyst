"""Extract rolling balance-sheet observations from SEC EDGAR."""

from datetime import date


BALANCE_SHEET_CONCEPTS = {
    "total_assets": "Assets",
    "total_liabilities": "Liabilities",
    "shareholders_equity": "StockholdersEquity",
    "cash_and_equivalents": "CashAndCashEquivalentsAtCarryingValue",
    "current_assets": "AssetsCurrent",
    "current_liabilities": "LiabilitiesCurrent",
    "long_term_debt": "LongTermDebt",
    "current_portion_long_term_debt": "LongTermDebtCurrent",
    "noncurrent_long_term_debt": "LongTermDebtNoncurrent",
    "short_term_borrowings": "ShortTermBorrowings",
    "commercial_paper": "CommercialPaper",
}


def select_balance_sheet_observations(
    observations: list[dict],
    limit: int = 12,
) -> list[dict]:
    """Select latest reported balance-sheet dates."""

    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")

    selected = {}

    for item in observations:
        if item.get("form") not in {
            "10-K", "10-K/A", "10-Q", "10-Q/A"
        }:
            continue

        # Balance-sheet facts are instant observations.
        if item.get("start") is not None:
            continue

        end = item.get("end")
        filed = item.get("filed")
        accn = item.get("accn")
        value = item.get("val")

        try:
            date.fromisoformat(end)
            date.fromisoformat(filed)
        except (TypeError, ValueError):
            continue

        if not accn:
            continue

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue

        existing = selected.get(end)

        if existing is None or (
            filed, accn
        ) > (
            existing["filed"], existing["accn"]
        ):
            selected[end] = item

    return sorted(
        selected.values(),
        key=lambda item: item["end"],
        reverse=True,
    )[:limit]


def extract_balance_sheet(
    company_facts: dict,
    periods: int = 12,
) -> dict:
    """Extract balance-sheet metrics with SEC filing provenance."""

    facts = company_facts.get("facts", {}).get("us-gaap", {})
    result = {}

    for metric_name, concept in BALANCE_SHEET_CONCEPTS.items():
        concept_data = facts.get(concept)

        if not concept_data:
            result[metric_name] = {
                "status": "unavailable",
                "concept": concept,
                "observations": [],
            }
            continue

        observations = concept_data.get("units", {}).get("USD", [])

        selected = select_balance_sheet_observations(
            observations,
            limit=periods,
        )

        result[metric_name] = {
            "status": "available" if selected else "unavailable",
            "concept": concept,
            "observations": selected,
        }

    return result
