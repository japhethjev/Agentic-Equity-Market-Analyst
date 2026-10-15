"""Integration tests for the Financial Analysis LangGraph workflow."""

from agents.financial_analysis_agent import financial_analysis_agent


def test_financial_analysis_agent_preserves_both_analysis_outputs():
    """The full graph produces separate profitability and liquidity results."""
    state = {
        "ticker": "TEST",
        "annual_income_statements": [],
        "quarterly_income_statements": [],
        "ttm_income_statements": [],
        "annual_cash_flows": [],
        "quarterly_cash_flows": [],
        "ttm_cash_flows": [],
        "balance_sheets": [],
    }

    result = financial_analysis_agent.invoke(state)

    assert result["ticker"] == "TEST"

    assert set(result["profitability"]) == {
        "annual", "quarterly", "ttm"
    }
    assert set(result["liquidity"]) == {
        "annual", "quarterly", "ttm"
    }

    assert result["validation"]["status"] == "validated"
    assert result["liquidity_validation"]["status"] == "validated"

    for period in ("annual", "quarterly", "ttm"):
        assert len(result["tables"][period]["rows"]) == 5
        assert len(result["liquidity_tables"][period]["rows"]) == 4

        assert result["tables"][period]["columns"] == [
            "Profitability Ratio"
        ]
        assert result["liquidity_tables"][period]["columns"] == [
            "Liquidity Ratio"
        ]


def test_financial_analysis_agent_calculates_real_ratios():
    """Verify financial calculations through the complete LangGraph workflow."""
    from decimal import Decimal

    def metric(value):
        return {"value": Decimal(str(value))}

    state = {
        "ticker": "TEST",
        "annual_income_statements": [{
            "period_start": "2025-01-01",
            "period_end": "2025-12-31",
            "metrics": {
                "revenue": metric(1000),
                "gross_profit": metric(400),
                "operating_income": metric(200),
                "net_income": metric(100),
            },
        }],
        "quarterly_income_statements": [],
        "ttm_income_statements": [],
        "annual_cash_flows": [{
            "period_start": "2025-01-01",
            "period_end": "2025-12-31",
            "period_type": "annual",
            "metrics": {
                "operating_cash_flow": {
                    "value": Decimal("150"),
                    "period_start": "2025-01-01",
                },
            },
        }],
        "quarterly_cash_flows": [],
        "ttm_cash_flows": [],
        "balance_sheets": [
            {
                "period_end": "2024-12-31",
                "metrics": {
                    "total_assets": metric(800),
                    "shareholders_equity": metric(400),
                    "current_liabilities": metric(200),
                },
            },
            {
                "period_end": "2025-12-31",
                "metrics": {
                    "total_assets": metric(1200),
                    "shareholders_equity": metric(600),
                    "current_assets": metric(500),
                    "current_liabilities": metric(300),
                    "inventory": metric(100),
                    "cash_and_equivalents": metric(150),
                },
            },
        ],
    }

    result = financial_analysis_agent.invoke(state)

    profitability = result["profitability"]["annual"][0]["metrics"]
    liquidity = result["liquidity"]["annual"][0]["metrics"]

    assert profitability["gross_profit_margin"]["value"] == Decimal("40")
    assert profitability["operating_profit_margin"]["value"] == Decimal("20")
    assert profitability["net_profit_margin"]["value"] == Decimal("10")
    assert profitability["return_on_assets"]["value"] == Decimal("10")
    assert profitability["return_on_equity"]["value"] == Decimal("20")

    assert liquidity["current_ratio"]["value"] == Decimal("500") / Decimal("300")
    assert liquidity["quick_ratio"]["value"] == Decimal("400") / Decimal("300")
    assert liquidity["cash_ratio"]["value"] == Decimal("0.5")
    assert liquidity["operating_cash_flow_ratio"]["value"] == Decimal("0.6")

    ocf = liquidity["operating_cash_flow_ratio"]
    assert ocf["denominator_method"] == "average_balance"
    assert ocf["annualized"] is False

    assert result["validation"]["status"] == "validated"
    assert result["liquidity_validation"]["status"] == "validated"

    assert result["tables"]["annual"]["rows"][0]["values"] == ["40.00%"]
    assert result["liquidity_tables"]["annual"]["rows"][0]["values"] == ["1.67x"]


def test_financial_analysis_agent_quarterly_ocf_annualization():
    """Quarterly OCF is annualized using average current liabilities."""
    from decimal import Decimal

    def metric(value):
        return {"value": Decimal(str(value))}

    state = {
        "ticker": "TEST",
        "annual_income_statements": [],
        "quarterly_income_statements": [{
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
            "metrics": {
                "revenue": metric(250),
                "gross_profit": metric(100),
                "operating_income": metric(50),
                "net_income": metric(25),
            },
        }],
        "ttm_income_statements": [],
        "annual_cash_flows": [],
        "quarterly_cash_flows": [{
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
            "period_type": "quarterly",
            "metrics": {
                "operating_cash_flow": {
                    "value": Decimal("30"),
                    "period_start": "2026-01-01",
                },
            },
        }],
        "ttm_cash_flows": [],
        "balance_sheets": [
            {
                "period_end": "2025-12-31",
                "metrics": {
                    "total_assets": metric(800),
                    "shareholders_equity": metric(400),
                    "current_liabilities": metric(100),
                },
            },
            {
                "period_end": "2026-03-31",
                "metrics": {
                    "total_assets": metric(1000),
                    "shareholders_equity": metric(500),
                    "current_assets": metric(280),
                    "current_liabilities": metric(140),
                    "inventory": metric(70),
                    "cash_and_equivalents": metric(56),
                },
            },
        ],
    }

    result = financial_analysis_agent.invoke(state)

    profitability = result["profitability"]["quarterly"][0]["metrics"]
    liquidity = result["liquidity"]["quarterly"][0]["metrics"]
    ocf = liquidity["operating_cash_flow_ratio"]

    assert profitability["gross_profit_margin"]["value"] == Decimal("40")
    assert profitability["net_profit_margin"]["value"] == Decimal("10")
    assert profitability["return_on_assets"]["status"] == "available"
    assert profitability["return_on_equity"]["status"] == "available"

    assert liquidity["current_ratio"]["value"] == Decimal("2")
    assert liquidity["quick_ratio"]["value"] == Decimal("1.5")
    assert liquidity["cash_ratio"]["value"] == Decimal("0.4")

    assert ocf["value"] == Decimal("1")
    assert ocf["denominator_method"] == "average_balance"
    assert ocf["annualized"] is True

    assert result["validation"]["status"] == "validated"
    assert result["liquidity_validation"]["status"] == "validated"
    assert result["liquidity_tables"]["quarterly"]["rows"][3]["values"] == [
        "1.00x"
    ]


def test_financial_analysis_agent_ttm_ocf_not_annualized():
    """TTM OCF uses the actual oldest quarter start and is not annualized."""
    from decimal import Decimal

    def metric(value):
        return {"value": Decimal(str(value))}

    quarter_dates = [
        ("2025-07-01", "2025-09-30"),
        ("2025-10-01", "2025-12-31"),
        ("2026-01-01", "2026-03-31"),
        ("2026-04-01", "2026-06-30"),
    ]

    quarters = [
        {
            "period_start": start,
            "period_end": end,
            "period_type": "quarterly",
            "metrics": {
                "operating_cash_flow": {
                    "value": Decimal("30"),
                    "period_start": start,
                },
            },
        }
        for start, end in quarter_dates
    ]

    state = {
        "ticker": "TEST",
        "annual_income_statements": [],
        "quarterly_income_statements": [],
        "ttm_income_statements": [{
            "period_start": "2025-07-01",
            "period_end": "2026-06-30",
            "metrics": {
                "revenue": metric(1000),
                "gross_profit": metric(400),
                "operating_income": metric(200),
                "net_income": metric(100),
            },
        }],
        "annual_cash_flows": [],
        "quarterly_cash_flows": quarters,
        "ttm_cash_flows": [{
            "period_end": "2026-06-30",
            "period_type": "ttm",
            "metrics": {
                "operating_cash_flow": {
                    "ttm": Decimal("120"),
                    "status": "available",
                    "quarters_used": [
                        end for _, end in quarter_dates
                    ],
                },
            },
        }],
        "balance_sheets": [
            {
                "period_end": "2025-06-30",
                "metrics": {
                    "total_assets": metric(800),
                    "shareholders_equity": metric(400),
                    "current_liabilities": metric(100),
                },
            },
            {
                "period_end": "2026-06-30",
                "metrics": {
                    "total_assets": metric(1200),
                    "shareholders_equity": metric(600),
                    "current_assets": metric(280),
                    "current_liabilities": metric(140),
                    "inventory": metric(70),
                    "cash_and_equivalents": metric(56),
                },
            },
        ],
    }

    result = financial_analysis_agent.invoke(state)

    profitability = result["profitability"]["ttm"][0]["metrics"]
    liquidity = result["liquidity"]["ttm"][0]["metrics"]
    ocf = liquidity["operating_cash_flow_ratio"]

    assert profitability["gross_profit_margin"]["value"] == Decimal("40")
    assert profitability["return_on_assets"]["value"] == Decimal("10")
    assert profitability["return_on_equity"]["value"] == Decimal("20")

    assert liquidity["current_ratio"]["value"] == Decimal("2")
    assert liquidity["quick_ratio"]["value"] == Decimal("1.5")
    assert liquidity["cash_ratio"]["value"] == Decimal("0.4")

    assert ocf["value"] == Decimal("1")
    assert ocf["denominator_method"] == "average_balance"
    assert ocf["annualized"] is False

    assert result["validation"]["status"] == "validated"
    assert result["liquidity_validation"]["status"] == "validated"
    assert result["liquidity_tables"]["ttm"]["rows"][3]["values"] == [
        "1.00x"
    ]
