"""Retrieve reported financial facts from SEC EDGAR."""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv


SEC_COMPANY_FACTS_URL = (
    "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
)


def get_company_facts(cik: int) -> dict:
    """Retrieve SEC Company Facts for a company CIK."""

    if isinstance(cik, bool) or not isinstance(cik, int) or cik <= 0:
        raise ValueError("CIK must be a positive integer.")

    load_dotenv(
        dotenv_path=Path(__file__).resolve().parents[2] / ".env"
    )

    user_agent = os.getenv("SEC_USER_AGENT", "").strip()

    if not user_agent:
        raise ValueError("SEC_USER_AGENT is not configured.")

    url = SEC_COMPANY_FACTS_URL.format(cik=f"{cik:010d}")

    response = requests.get(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("cik") != cik:
        raise ValueError("SEC response CIK does not match request.")

    if not isinstance(data.get("facts"), dict):
        raise ValueError("SEC response contains no financial facts.")

    return data


def get_financial_concept(
    company_facts: dict,
    concept: str,
    unit: str = "USD",
) -> list[dict]:
    """Return observations for a specified US-GAAP concept."""

    facts = company_facts.get("facts", {}).get("us-gaap", {})

    concept_data = facts.get(concept)

    if concept_data is None:
        raise ValueError(f"Financial concept unavailable: {concept}")

    observations = concept_data.get("units", {}).get(unit)

    if observations is None:
        raise ValueError(
            f"Unit {unit} unavailable for concept {concept}"
        )

    return observations
