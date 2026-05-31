from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from services.pipeline import AnalystCopilotPipeline

load_dotenv()

st.set_page_config(page_title="Analyst Copilot", page_icon="📊", layout="wide")

root = Path(__file__).resolve().parents[1]
pipeline = AnalystCopilotPipeline(root)

st.title("Analyst Copilot Report Generator")
st.caption("Generate Geojit-style financial research reports with confidence and source traceability.")

col1, col2 = st.columns([2, 1])
with col1:
    company_name = st.text_input("Company Name", placeholder="Example: ICICI Bank")
with col2:
    st.markdown("**Supported input formats**")
    st.write("PDF, CSV, TXT")

uploaded_files = st.file_uploader(
    "Upload context documents",
    type=["pdf", "csv", "txt", "md"],
    accept_multiple_files=True,
)

generate = st.button("Generate Report", type="primary", use_container_width=True)

if generate:
    if not company_name.strip():
        st.error("Please enter a company name.")
    elif not uploaded_files:
        st.error("Please upload at least one context file.")
    else:
        with st.spinner("Analyzing documents and generating report..."):
            report, pdf_bytes = pipeline.run(company_name.strip(), uploaded_files)

        st.success("Report generated.")

        quality_flags = [m for m in report.key_metrics if m.confidence < 0.55]
        missing_core = 0
        for field in [report.outlook, report.risks, report.valuation]:
            if not field:
                missing_core += 1

        q1, q2, q3 = st.columns(3)
        q1.metric("Metrics extracted", len(report.key_metrics))
        q2.metric("Low-confidence metrics", len(quality_flags))
        q3.metric("Missing narrative blocks", missing_core)
        quality = report.table_quality if isinstance(report.table_quality, dict) else {}
        st.caption(
            " | ".join(
                [
                    f"Table coverage: {quality.get('completeness', 0)}",
                    f"Merged rows: {quality.get('merged_rows', 0)}",
                    f"Chart basis: {report.chart_basis or 'Will be shown in PDF chart section'}",
                ]
            )
        )

        st.subheader("Headline")
        st.write(report.headline)

        st.subheader("Highlights")
        for item in report.highlights[:6]:
            st.write(f"- {item}")

        st.subheader("Confidence and Sources")
        if report.key_metrics:
            rows = []
            for metric in report.key_metrics:
                rows.append(
                    {
                        "Metric": metric.name,
                        "Value": f"{metric.value} {metric.unit}".strip(),
                        "Confidence": round(metric.confidence, 2),
                        "Source Page": metric.source_page,
                        "Source Excerpt": metric.source_excerpt,
                        "Assumption": metric.assumption,
                    }
                )
            st.dataframe(rows, use_container_width=True)
        else:
            st.info("No metric-level evidence rows were returned.")

        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name=f"{company_name.strip().replace(' ', '_')}_analyst_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        with st.expander("View raw extraction JSON"):
            st.code(json.dumps(report.raw_extraction, indent=2), language="json")

st.markdown("---")
st.markdown("Built for Bull AI Software Engineer assessment.")
