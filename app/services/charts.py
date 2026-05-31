from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .models import ReportData


@dataclass
class ChartBuildResult:
    chart_path: Path
    chart_basis: str


def _to_float(value: str) -> float | None:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", value)
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _safe_stem(company_name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", company_name).strip("_").lower()
    return cleaned or "company"


def _build_trend_chart(periods: list[str], revenue_values: list[float], chart_path: Path) -> None:
    plt.figure(figsize=(7, 3.4))
    plt.plot(periods, revenue_values, marker="o", linewidth=2.0, color="#145A7A")
    plt.title("Revenue Trend")
    plt.xlabel("Period")
    plt.ylabel("Revenue")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(chart_path, dpi=160)
    plt.close()


def _build_snapshot_chart(labels: list[str], values: list[float], chart_path: Path) -> None:
    plt.figure(figsize=(7, 3.4))
    bars = plt.bar(labels, values, color=["#145A7A", "#2B8CBE", "#74A9CF"][: len(labels)])
    plt.title("Financial Snapshot")
    plt.ylabel("Value")
    for bar, value in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:.2f}", ha="center", va="bottom", fontsize=8)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(chart_path, dpi=160)
    plt.close()


def _build_placeholder_chart(chart_path: Path) -> None:
    plt.figure(figsize=(7, 3.4))
    plt.axis("off")
    plt.text(0.5, 0.55, "Chart generated with limited numeric data", ha="center", va="center", fontsize=11)
    plt.text(0.5, 0.4, "Upload richer tabular context for trend visuals", ha="center", va="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(chart_path, dpi=160)
    plt.close()


def build_revenue_chart(report: ReportData, output_dir: Path) -> ChartBuildResult:
    periods: list[str] = []
    revenue_values: list[float] = []

    for row in report.financial_table:
        value = _to_float(row.revenue)
        if value is None:
            continue
        periods.append(row.period)
        revenue_values.append(value)

    output_dir.mkdir(parents=True, exist_ok=True)
    chart_path = output_dir / f"{_safe_stem(report.company_name)}_chart.png"

    if len(revenue_values) >= 2:
        _build_trend_chart(periods, revenue_values, chart_path)
        return ChartBuildResult(chart_path=chart_path, chart_basis="Revenue trend from multi-period financial table.")

    snapshot_labels: list[str] = []
    snapshot_values: list[float] = []

    if report.financial_table:
        row = report.financial_table[-1]
        for label, raw in [("Revenue", row.revenue), ("EBITDA", row.ebitda), ("PAT", row.pat)]:
            value = _to_float(raw)
            if value is not None:
                snapshot_labels.append(label)
                snapshot_values.append(value)

    if not snapshot_values:
        for metric in report.key_metrics:
            label = metric.name.strip().upper()
            if not any(token in label for token in ("REVENUE", "EBITDA", "PAT", "NET PROFIT")):
                continue
            value = _to_float(metric.value)
            if value is None:
                continue
            snapshot_labels.append(metric.name.strip())
            snapshot_values.append(value)
            if len(snapshot_values) >= 3:
                break

    if snapshot_values:
        _build_snapshot_chart(snapshot_labels, snapshot_values, chart_path)
        return ChartBuildResult(
            chart_path=chart_path,
            chart_basis="Single-period metric snapshot (trend not available in source).",
        )

    _build_placeholder_chart(chart_path)
    return ChartBuildResult(
        chart_path=chart_path,
        chart_basis="Placeholder chart due to insufficient numeric data in extracted content.",
    )
