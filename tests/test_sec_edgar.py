"""Tests for SEC EDGAR financial data retrieval."""

from unittest.mock import Mock, patch

import pytest
import requests

from tools.financial_statements.sec_edgar import (
    get_company_facts,
    get_financial_concept,
)


@pytest.fixture
def sample_facts():
    return {
        "cik": 320193,
        "entityName": "Apple Inc.",
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {
                                "val": 1000000,
                                "start": "2025-01-01",
                                "end": "2025-12-31",
                                "form": "10-K",
                                "filed": "2026-02-01",
                                "accn": "0000000000-26-000001",
                            }
                        ]
                    }
                }
            }
        },
    }


def test_get_company_facts_success(sample_facts, monkeypatch):
    monkeypatch.setenv(
        "SEC_USER_AGENT",
        "Test Research test@example.com",
    )

    response = Mock()
    response.json.return_value = sample_facts
    response.raise_for_status.return_value = None

    with patch(
        "tools.financial_statements.sec_edgar.requests.get",
        return_value=response,
    ) as mock_get:
        result = get_company_facts(320193)

    assert result["entityName"] == "Apple Inc."
    assert mock_get.call_args.kwargs["timeout"] == 30


def test_invalid_cik():
    with pytest.raises(ValueError, match="CIK"):
        get_company_facts(0)


def test_boolean_cik_rejected():
    with pytest.raises(ValueError, match="CIK"):
        get_company_facts(True)


def test_missing_user_agent(monkeypatch):
    monkeypatch.setenv("SEC_USER_AGENT", "")

    with pytest.raises(ValueError, match="SEC_USER_AGENT"):
        get_company_facts(320193)


def test_sec_http_error(monkeypatch):
    monkeypatch.setenv(
        "SEC_USER_AGENT",
        "Test Research test@example.com",
    )

    response = Mock()
    response.raise_for_status.side_effect = (
        requests.exceptions.HTTPError("403 Forbidden")
    )

    with patch(
        "tools.financial_statements.sec_edgar.requests.get",
        return_value=response,
    ):
        with pytest.raises(requests.exceptions.HTTPError):
            get_company_facts(320193)


def test_sec_cik_mismatch(sample_facts, monkeypatch):
    monkeypatch.setenv(
        "SEC_USER_AGENT",
        "Test Research test@example.com",
    )

    sample_facts["cik"] = 999999

    response = Mock()
    response.json.return_value = sample_facts

    with patch(
        "tools.financial_statements.sec_edgar.requests.get",
        return_value=response,
    ):
        with pytest.raises(ValueError, match="CIK does not match"):
            get_company_facts(320193)


def test_extract_financial_concept(sample_facts):
    observations = get_financial_concept(
        sample_facts,
        "Revenues",
    )

    assert len(observations) == 1
    assert observations[0]["val"] == 1000000


def test_missing_financial_concept(sample_facts):
    with pytest.raises(ValueError, match="unavailable"):
        get_financial_concept(
            sample_facts,
            "NonexistentConcept",
        )
