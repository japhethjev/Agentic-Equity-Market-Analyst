"""Standardised SEC income-statement concept mapping."""

INCOME_STATEMENT_CONCEPTS = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ],
    "cost_of_revenue": [
        "CostOfGoodsAndServicesSold",
    ],
    "gross_profit": [
        "GrossProfit",
    ],
    "operating_expenses": [
        "OperatingExpenses",
    ],
    "research_and_development": [
        "ResearchAndDevelopmentExpense",
    ],
    "selling_general_administrative": [
        "SellingGeneralAndAdministrativeExpense",
    ],
    "operating_income": [
        "OperatingIncomeLoss",
    ],
    "pretax_income": [
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
    ],
    "income_tax_expense": [
        "IncomeTaxExpenseBenefit",
    ],
    "net_income": [
        "NetIncomeLoss",
    ],
    "basic_eps": [
        "EarningsPerShareBasic",
    ],
    "diluted_eps": [
        "EarningsPerShareDiluted",
    ],
    "basic_weighted_average_shares": [
        "WeightedAverageNumberOfSharesOutstandingBasic",
    ],
    "diluted_weighted_average_shares": [
        "WeightedAverageNumberOfDilutedSharesOutstanding",
    ],
}

METRIC_UNITS = {
    "basic_eps": "USD/shares",
    "diluted_eps": "USD/shares",
    "basic_weighted_average_shares": "shares",
    "diluted_weighted_average_shares": "shares",
}


def extract_income_statement_concepts(company_facts: dict) -> dict:
    """Select available US-GAAP concepts without mixing alternatives."""

    facts = company_facts.get("facts", {}).get("us-gaap", {})
    result = {}

    for metric, candidates in INCOME_STATEMENT_CONCEPTS.items():
        unit = METRIC_UNITS.get(metric, "USD")

        selected_concept = None
        observations = []

        for concept in candidates:
            records = facts.get(concept, {}).get("units", {}).get(unit, [])

            if records:
                selected_concept = concept
                observations = records
                break

        result[metric] = {
            "concept": selected_concept,
            "unit": unit,
            "status": "available" if observations else "unavailable",
            "reported_observations": observations,
        }

    return result
