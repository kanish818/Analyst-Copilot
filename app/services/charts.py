from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt

from .models import ReportData


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


def build_revenue_chart(report: ReportData, output_dir: Path) -> Path | None:
    periods: list[str] = []
    revenue_values: list[float] = []

    for row in report.financial_table:
        value = _to_float(row.revenue)
        if value is None:
            continue
        periods.append(row.period)
        revenue_values.append(value)

    if len(revenue_values) < 2:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    chart_path = output_dir / "revenue_trend.png"

    plt.figure(figsize=(7, 3.4))
    plt.plot(periods, revenue_values, marker="o", linewidth=2.0, color="#145A7A")
    plt.title("Revenue Trend")
    plt.xlabel("Period")
    plt.ylabel("Revenue")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(chart_path, dpi=160)
    plt.close()

    return chart_path
