from __future__ import annotations

from pathlib import Path
from typing import Any

from .charts import build_revenue_chart
from .extractor import extract_financial_payload
from .ingest import IngestResult, ingest_uploaded_files
from .mapper import map_payload_to_report
from .models import ReportData
from .pdf_report import render_report_pdf


class AnalystCopilotPipeline:
    def __init__(self, working_dir: Path):
        self.working_dir = working_dir
        self.chart_dir = working_dir / "data" / "outputs" / "charts"

    def ingest(self, uploaded_files: list[Any]) -> IngestResult:
        return ingest_uploaded_files(uploaded_files)

    def extract(self, company_name: str, ingest_result: IngestResult) -> dict[str, Any]:
        return extract_financial_payload(company_name, ingest_result.combined_text)

    def map_report(self, company_name: str, payload: dict[str, Any]) -> ReportData:
        return map_payload_to_report(company_name, payload)

    def build_pdf(self, report: ReportData) -> bytes:
        chart_result = build_revenue_chart(report, self.chart_dir)
        report.chart_basis = chart_result.chart_basis
        return render_report_pdf(report, chart_result.chart_path)

    def run(self, company_name: str, uploaded_files: list[Any]) -> tuple[ReportData, bytes]:
        ingest_result = self.ingest(uploaded_files)
        payload = self.extract(company_name, ingest_result)
        report = self.map_report(company_name, payload)
        pdf_bytes = self.build_pdf(report)
        return report, pdf_bytes
