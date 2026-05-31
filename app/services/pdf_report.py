from __future__ import annotations

import io
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import ReportData


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleStyle",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#0B2239"),
            spaceAfter=6,
        ),
        "section": ParagraphStyle(
            "SectionStyle",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0B2239"),
            spaceBefore=6,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "BodyStyle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
        ),
        "small": ParagraphStyle(
            "SmallStyle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#2F3B47"),
        ),
    }


def _table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5EEF5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0B2239")),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#A9B7C5")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FBFD")]),
        ]
    )


def render_report_pdf(report: ReportData, chart_path: Path | None = None) -> bytes:
    styles = _styles()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=14 * mm,
        bottomMargin=12 * mm,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        title=f"{report.company_name} Analyst Report",
    )

    story = []

    story.append(Paragraph(f"{report.company_name} - Analyst Copilot Report", styles["title"]))
    meta = f"Date: {report.report_date} | Sector: {report.sector or 'N/A'} | Recommendation: {report.recommendation}"
    story.append(Paragraph(meta, styles["small"]))
    story.append(Spacer(1, 5))

    if report.headline:
        story.append(Paragraph(report.headline, styles["body"]))
        story.append(Spacer(1, 6))

    if report.current_price or report.target_price:
        story.append(Paragraph("<b>Price Snapshot</b>", styles["section"]))
        price_table = Table(
            [
                ["Current Price", "Target Price"],
                [report.current_price or "N/A", report.target_price or "N/A"],
            ],
            colWidths=[75 * mm, 75 * mm],
        )
        price_table.setStyle(_table_style())
        story.append(price_table)
        story.append(Spacer(1, 6))

    story.append(Paragraph("Investment Highlights", styles["section"]))
    if report.highlights:
        for bullet in report.highlights[:6]:
            story.append(Paragraph(f"- {bullet}", styles["body"]))
    else:
        story.append(Paragraph("- No structured highlights extracted.", styles["body"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Financial Table", styles["section"]))
    fin_header = ["Period", "Revenue", "EBITDA", "PAT", "EBITDA Margin"]
    fin_rows = [fin_header]
    for row in report.financial_table:
        fin_rows.append([row.period, row.revenue or "", row.ebitda or "", row.pat or "", row.ebitda_margin or ""])

    if len(fin_rows) == 1:
        fin_rows.append(["N/A", "", "", "", ""])

    fin_table = Table(fin_rows, colWidths=[26 * mm, 34 * mm, 30 * mm, 30 * mm, 34 * mm])
    fin_table.setStyle(_table_style())
    story.append(fin_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Chart", styles["section"]))
    if chart_path and chart_path.exists():
        chart = Image(str(chart_path), width=165 * mm, height=65 * mm)
        story.append(chart)
        basis = report.chart_basis or "Chart basis unavailable."
        story.append(Paragraph(f"Chart Basis: {basis}", styles["small"]))
    else:
        story.append(Paragraph("Chart unavailable in this run.", styles["small"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Outlook & Valuation", styles["section"]))
    story.append(Paragraph(f"<b>Outlook:</b> {report.outlook or 'Outlook not available from source content.'}", styles["body"]))
    story.append(Spacer(1, 2))
    story.append(Paragraph(f"<b>Valuation:</b> {report.valuation or 'Valuation commentary not available from source content.'}", styles["body"]))
    story.append(Spacer(1, 2))
    story.append(Paragraph(f"<b>Risks:</b> {report.risks or 'Risk disclosure not available from source content.'}", styles["body"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Key Metrics with Confidence", styles["section"]))
    metric_header = ["Metric", "Value", "Trend", "Confidence", "Source (Page)", "Assumption"]
    metric_rows = [metric_header]
    for metric in report.key_metrics:
        metric_rows.append(
            [
                metric.name,
                f"{metric.value} {metric.unit}".strip(),
                metric.trend,
                f"{metric.confidence:.2f}",
                (metric.source_page or "")[:30],
                (metric.assumption or "")[:80],
            ]
        )

    if len(metric_rows) == 1:
        metric_rows.append(["N/A", "", "", "", "", ""])

    metric_table = Table(metric_rows, colWidths=[25 * mm, 25 * mm, 22 * mm, 18 * mm, 26 * mm, 49 * mm])
    metric_table.setStyle(_table_style())
    story.append(metric_table)
    story.append(Spacer(1, 6))

    if report.table_quality:
        quality_summary = (
            f"Table Coverage: {report.table_quality.get('completeness', 0)} | "
            f"Rows(Merged/Parser/LLM): {report.table_quality.get('merged_rows', 0)}/"
            f"{report.table_quality.get('parser_rows', 0)}/{report.table_quality.get('llm_rows', 0)}"
        )
        story.append(Paragraph(quality_summary, styles["small"]))
        story.append(Spacer(1, 6))

    story.append(Paragraph("Citations", styles["section"]))
    citations_header = ["Field", "Page", "Source Excerpt"]
    citation_rows = [citations_header]
    for item in report.citations[:12]:
        citation_rows.append(
            [
                str(item.get("field", ""))[:24],
                str(item.get("source_page", ""))[:20],
                str(item.get("source_excerpt", ""))[:120],
            ]
        )

    if len(citation_rows) == 1:
        citation_rows.append(["N/A", "", "No citation entries returned by extraction."])

    citation_table = Table(citation_rows, colWidths=[35 * mm, 25 * mm, 120 * mm])
    citation_table.setStyle(_table_style())
    story.append(citation_table)

    doc.build(story)
    return buffer.getvalue()
