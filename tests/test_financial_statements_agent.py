"""Regression tests for the Financial Statements Agent."""

from agents.financial_statements_agent import (
    financial_statements_agent,
)


def test_financial_statements_workflow_structure():
    """Ensure validation precedes financial presentation."""
    graph = financial_statements_agent.get_graph()

    nodes = set(graph.nodes)
    expected = {
        "retrieve_company_facts",
        "construct_income_statements",
        "construct_balance_sheets",
        "construct_quarterly_cash_flows",
        "construct_ttm_cash_flows",
        "validate_financial_statements",
        "present_financial_statements",
    }

    assert expected <= nodes

    edges = {(edge.source, edge.target) for edge in graph.edges}

    assert (
        "construct_ttm_cash_flows",
        "validate_financial_statements",
    ) in edges

    assert (
        "validate_financial_statements",
        "present_financial_statements",
    ) in edges


def test_financial_statements_workflow_execution(monkeypatch):
    """Verify node execution order without SEC network calls."""
    import agents.financial_statements_agent as module

    calls = []
    names = [
        "retrieve_company_facts",
        "construct_income_statements",
        "construct_balance_sheets",
        "construct_quarterly_cash_flows",
        "construct_ttm_cash_flows",
        "validate_financial_statements",
        "present_financial_statements",
    ]

    for name in names:
        def mock_node(state, node_name=name):
            calls.append(node_name)
            return {}

        monkeypatch.setattr(module, name, mock_node)

    agent = module.build_financial_statements_agent()
    result = agent.invoke({"ticker": "TEST", "cik": 123456})

    assert calls == names
    assert result["ticker"] == "TEST"
    assert result["cik"] == 123456


def test_all_six_financial_tables():
    """Verify six tables and preservation of missing TTM values."""
    from decimal import Decimal
    from tools.financial_statements.agent_presentation import (
        prepare_financial_statement_tables,
    )

    standard = {
        "period_end": "2026-06-30",
        "metrics": {"revenue": {"value": Decimal("200000000")}},
    }
    cash = {
        "period_end": "2026-06-30",
        "metrics": {
            "operating_cash_flow": {
                "status": "available",
                "ttm": Decimal("400000000"),
            },
            "common_stock_dividends": {
                "status": "insufficient_data",
                "ttm": None,
            },
        },
    }

    keys = (
        "annual_income_statements",
        "quarterly_income_statements",
        "ttm_income_statements",
        "balance_sheets",
        "quarterly_cash_flows",
    )
    state = {key: [standard] for key in keys}
    state["ttm_cash_flows"] = [cash]

    tables = prepare_financial_statement_tables(state)

    assert len(tables) == 6
    assert all(t["periods"] == ["2026-06-30"] for t in tables.values())

    rows = {
        row["metric"]: row
        for row in tables["ttm_cash_flow"]["rows"]
    }
    assert rows["operating_cash_flow"]["values"] == ["400"]
    assert rows["common_stock_dividends"]["values"] == [None]


def test_consolidated_validation_status(monkeypatch):
    """Distinguish valid data, missing data and failed checks."""
    import tools.financial_statements.agent_validation as module

    monkeypatch.setattr(
        module, "validate_agent_income_statements",
        lambda state: {
            "annual_income": [{"status": "validated"}],
            "quarterly_income": [{"status": "validated"}],
        },
    )
    monkeypatch.setattr(
        module, "validate_agent_balance_sheets",
        lambda state: [{"status": "pass"}],
    )
    monkeypatch.setattr(
        module, "validate_agent_ttm_cash_flows",
        lambda state: [{"status": "insufficient_data"}],
    )

    result = module.validate_all_financial_statements({})

    assert result["status"] == "validated_with_gaps"
    assert result["checks_passed"] == 3
    assert result["checks_missing"] == 1
    assert result["checks_failed"] == 0

    monkeypatch.setattr(
        module, "validate_agent_balance_sheets",
        lambda state: [{"status": "review_required"}],
    )

    result = module.validate_all_financial_statements({})

    assert result["status"] == "review_required"
    assert result["checks_failed"] == 1
