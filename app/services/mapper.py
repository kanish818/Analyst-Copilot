from __future__ import annotations

from typing import Any

from .models import FinancialRow, MetricEvidence, ReportData
from .utils import (
    clean_text,
    first_non_empty,
    normalize_confidence,
    normalize_metric_value,
    safe_list,
    today_label,
)


def map_payload_to_report(company_name: str, payload: dict[str, Any]) -> ReportData:
    highlights = [clean_text(item) for item in safe_list(payload.get("highlights")) if clean_text(item)]

    financial_rows: list[FinancialRow] = []
    for row in safe_list(payload.get("financial_table")):
        if not isinstance(row, dict):
            continue
        period = clean_text(row.get("period"))
        if not period:
            continue
        financial_rows.append(
            FinancialRow(
                period=period,
                revenue=clean_text(row.get("revenue")),
                ebitda=clean_text(row.get("ebitda")),
                pat=clean_text(row.get("pat")),
                ebitda_margin=clean_text(row.get("ebitda_margin")),
                source=clean_text(row.get("source")),
                source_page=clean_text(row.get("source_page")),
                row_completeness=_row_completeness(row),
            )
        )

    metric_rows: list[MetricEvidence] = []
    for metric in safe_list(payload.get("key_metrics")):
        if not isinstance(metric, dict):
            continue
        name = clean_text(metric.get("name"))
        if not name:
            continue
        metric_rows.append(
            MetricEvidence(
                name=name,
                value=normalize_metric_value(metric.get("value")),
                unit=clean_text(metric.get("unit")),
                trend=clean_text(metric.get("trend")),
                confidence=normalize_confidence(metric.get("confidence")),
                source_excerpt=clean_text(metric.get("source_excerpt")),
                source_page=clean_text(metric.get("source_page")),
                assumption=clean_text(metric.get("assumption")),
            )
        )

    citations = [c for c in safe_list(payload.get("citations")) if isinstance(c, dict)]

    recommendation = first_non_empty(payload.get("recommendation"), "Neutral")
    headline = first_non_empty(payload.get("headline"), f"{company_name}: Financial Update")

    return ReportData(
        company_name=company_name,
        report_date=today_label(),
        sector=clean_text(payload.get("sector")),
        headline=headline,
        recommendation=recommendation,
        current_price=clean_text(payload.get("current_price")),
        target_price=clean_text(payload.get("target_price")),
        highlights=highlights,
        financial_table=financial_rows,
        key_metrics=metric_rows,
        outlook=clean_text(payload.get("outlook")),
        risks=clean_text(payload.get("risks")),
        valuation=clean_text(payload.get("valuation")),
        citations=citations,
        table_quality=payload.get("table_quality", {}) if isinstance(payload.get("table_quality"), dict) else {},
        chart_basis=clean_text(payload.get("chart_basis")),
        raw_extraction=payload,
    )


def _row_completeness(row: dict[str, Any]) -> float:
    total = 4
    filled = 0
    for field in ("revenue", "ebitda", "pat", "ebitda_margin"):
        if clean_text(row.get(field)):
            filled += 1
    return round(filled / total, 2)
