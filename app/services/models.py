from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricEvidence:
    name: str
    value: str
    unit: str = ""
    trend: str = ""
    confidence: float = 0.0
    source_excerpt: str = ""
    source_page: str = ""
    assumption: str = ""


@dataclass
class FinancialRow:
    period: str
    revenue: str = ""
    ebitda: str = ""
    pat: str = ""
    ebitda_margin: str = ""


@dataclass
class ReportData:
    company_name: str
    report_date: str
    sector: str = ""
    headline: str = ""
    recommendation: str = ""
    current_price: str = ""
    target_price: str = ""
    highlights: list[str] = field(default_factory=list)
    financial_table: list[FinancialRow] = field(default_factory=list)
    key_metrics: list[MetricEvidence] = field(default_factory=list)
    outlook: str = ""
    risks: str = ""
    valuation: str = ""
    citations: list[dict[str, Any]] = field(default_factory=list)
    raw_extraction: dict[str, Any] = field(default_factory=dict)
