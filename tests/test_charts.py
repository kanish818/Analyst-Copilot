from pathlib import Path

from app.services.charts import build_revenue_chart
from app.services.models import FinancialRow, ReportData


def _report() -> ReportData:
    return ReportData(company_name="DemoCo", report_date="31 May 2026")


def test_build_revenue_chart_creates_trend_chart(tmp_path: Path):
    report = _report()
    report.financial_table = [
        FinancialRow(period="Q1FY26", revenue="100", ebitda="20", pat="10"),
        FinancialRow(period="Q2FY26", revenue="120", ebitda="24", pat="12"),
    ]
    result = build_revenue_chart(report, tmp_path)
    assert result.chart_path.exists()
    assert "trend" in result.chart_basis.lower()


def test_build_revenue_chart_creates_snapshot_for_single_period(tmp_path: Path):
    report = _report()
    report.financial_table = [FinancialRow(period="Q2FY26", revenue="120", ebitda="24", pat="12")]
    result = build_revenue_chart(report, tmp_path)
    assert result.chart_path.exists()
    assert "snapshot" in result.chart_basis.lower() or "single-period" in result.chart_basis.lower()
