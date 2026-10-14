"""Standardised financial statement data models."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal


StatementType = Literal[
    "income_statement",
    "balance_sheet",
    "cash_flow_statement",
]

PeriodType = Literal[
    "annual",
    "quarterly",
    "half_year",
]


@dataclass(frozen=True)
class FinancialMetric:
    company_name: str
    ticker: str
    metric_name: str
    value: Decimal
    currency: str
    statement_type: StatementType
    period_type: PeriodType
    period_end: date
    source_document: str
    source_page: int | None = None
    source_url: str | None = None

    def __post_init__(self):
        if not self.company_name.strip():
            raise ValueError("Company name is required.")

        if not self.ticker.strip():
            raise ValueError("Ticker is required.")

        if not self.metric_name.strip():
            raise ValueError("Metric name is required.")

        if len(self.currency) != 3:
            raise ValueError(
                "Currency must be a three-letter ISO code."
            )

        if not self.value.is_finite():
            raise ValueError("Metric value must be finite.")

        if not self.source_document.strip():
            raise ValueError("Source document is required.")

        if self.source_page is not None and self.source_page < 1:
            raise ValueError(
                "Source page must be a positive integer."
            )
