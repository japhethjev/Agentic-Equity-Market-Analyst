"""Extract SEC cash-flow metrics and standalone quarterly observations."""

from tools.financial_statements.cash_flow_reconstruction import (
    reconstruct_quarterly_cash_flows,
)


CASH_FLOW_CONCEPTS = {
    "operating_cash_flow": "NetCashProvidedByUsedInOperatingActivities",
    "capital_expenditure": "PaymentsToAcquirePropertyPlantAndEquipment",
    "investing_cash_flow": "NetCashProvidedByUsedInInvestingActivities",
    "financing_cash_flow": "NetCashProvidedByUsedInFinancingActivities",
    "dividends_paid": "PaymentsOfDividends",
    "common_stock_dividends": "PaymentsOfDividendsCommonStock",
    "share_repurchases": "PaymentsForRepurchaseOfCommonStock",
    "depreciation_amortisation": "DepreciationDepletionAndAmortization",
}


def extract_cash_flow(
    company_facts: dict,
    quarters: int = 12,
) -> dict:
    """Return SEC-reported and reconstructed quarterly cash-flow data."""

    if isinstance(quarters, bool) or not isinstance(quarters, int) or quarters < 1:
        raise ValueError("quarters must be a positive integer")

    facts = company_facts.get("facts", {}).get("us-gaap", {})
    result = {}

    for metric_name, concept in CASH_FLOW_CONCEPTS.items():
        concept_data = facts.get(concept, {})
        observations = concept_data.get("units", {}).get("USD", [])

        reconstructed = reconstruct_quarterly_cash_flows(observations)

        result[metric_name] = {
            "concept": concept,
            "status": "available" if reconstructed else "unavailable",
            "reported_observations": observations,
            "quarterly_observations": reconstructed[:quarters],
        }

    return result
