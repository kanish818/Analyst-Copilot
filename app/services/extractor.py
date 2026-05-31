from __future__ import annotations

import os
import re
from typing import Any

import httpx
from openai import OpenAI

from .financial_parser import derive_row_from_key_metrics, merge_financial_rows, parse_financial_rows_from_text
from .utils import extract_json_object


SYSTEM_PROMPT = """
You are a financial research assistant. Extract verifiable facts from source text.
Return only valid JSON with this shape:
{
  "sector": "",
  "headline": "",
  "recommendation": "Buy/Hold/Reduce/Neutral",
  "current_price": "",
  "target_price": "",
  "highlights": ["..."],
  "financial_table": [
    {"period": "Q1FY26", "revenue": "", "ebitda": "", "pat": "", "ebitda_margin": "", "source": "llm", "source_page": ""}
  ],
  "key_metrics": [
    {
      "name": "",
      "value": "",
      "unit": "",
      "trend": "",
      "confidence": 0.0,
      "source_excerpt": "",
      "source_page": "",
      "assumption": ""
    }
  ],
  "outlook": "",
  "risks": "",
  "valuation": "",
  "citations": [
    {"field": "", "source_page": "", "source_excerpt": ""}
  ]
}
Rules:
- Use only data found in source text.
- If unavailable, keep empty string.
- confidence range must be 0.0 to 1.0.
- source_page should reference page markers like PAGE 3 when present.
- Keep highlights to 4-6 bullets.
- Extract up to 4 recent periods when available in the source.
""".strip()


def _groq_client() -> OpenAI | None:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        return None
    try:
        http_client = httpx.Client(timeout=60.0, follow_redirects=True, trust_env=True)
        return OpenAI(
            api_key=key,
            base_url="https://api.groq.com/openai/v1",
            http_client=http_client,
        )
    except Exception:
        return None


def _heuristic_fallback(company_name: str, context_text: str) -> dict[str, Any]:
    lines = [ln.strip() for ln in context_text.splitlines() if ln.strip()]
    highlights = []
    for ln in lines:
        if len(ln) > 40 and any(token in ln.lower() for token in ["revenue", "profit", "growth", "ebitda", "margin"]):
            highlights.append(ln[:180])
        if len(highlights) >= 5:
            break

    # Try simple pattern extraction for a few common metrics.
    metrics: list[dict[str, Any]] = []
    patterns = {
        "Revenue": r"revenue[^\n]{0,80}?([0-9][0-9,\.]+)",
        "EBITDA": r"ebitda[^\n]{0,80}?([0-9][0-9,\.]+)",
        "PAT": r"(?:pat|net profit)[^\n]{0,80}?([0-9][0-9,\.]+)",
    }

    lower_text = context_text.lower()
    for name, pattern in patterns.items():
        match = re.search(pattern, lower_text, flags=re.IGNORECASE)
        if not match:
            continue
        value = match.group(1)
        metrics.append(
            {
                "name": name,
                "value": value,
                "unit": "",
                "trend": "",
                "confidence": 0.45,
                "source_excerpt": match.group(0)[:140],
                "source_page": "",
                "assumption": "Heuristic extraction due to unavailable LLM response.",
            }
        )

    return {
        "sector": "",
        "headline": f"{company_name}: Auto-generated analyst draft",
        "recommendation": "Neutral",
        "current_price": "",
        "target_price": "",
        "highlights": highlights or ["Limited data extracted from the uploaded files."],
        "financial_table": [],
        "key_metrics": metrics,
        "outlook": "Outlook generated from available source snippets only.",
        "risks": "Missing structured financial fields in source or extraction response.",
        "valuation": "Insufficient valuation inputs from parsed content.",
        "citations": [
            {
                "field": "highlights",
                "source_page": "",
                "source_excerpt": (highlights[0] if highlights else "No high-confidence source snippet available."),
            }
        ],
    }


def extract_financial_payload(company_name: str, context_text: str) -> dict[str, Any]:
    text = context_text[:50000]
    user_prompt = f"Company: {company_name}\n\nSource Context:\n{text}"

    client = _groq_client()
    if not client:
        payload = _heuristic_fallback(company_name, context_text)
        return _enrich_financial_table(payload, context_text)

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = (resp.choices[0].message.content or "").strip()
        payload = extract_json_object(content)
        if payload:
            return _enrich_financial_table(payload, context_text)
    except Exception:
        pass

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = (resp.choices[0].message.content or "").strip()
        payload = extract_json_object(content)
        if payload:
            return _enrich_financial_table(payload, context_text)
    except Exception:
        pass

    payload = _heuristic_fallback(company_name, context_text)
    return _enrich_financial_table(payload, context_text)


def _enrich_financial_table(payload: dict[str, Any], context_text: str) -> dict[str, Any]:
    llm_rows = payload.get("financial_table")
    llm_rows = llm_rows if isinstance(llm_rows, list) else []

    parser_rows = parse_financial_rows_from_text(context_text)
    merged_rows = merge_financial_rows(parser_rows, llm_rows)

    if not merged_rows:
        key_metric_rows = derive_row_from_key_metrics(payload.get("key_metrics", []), context_text)
        merged_rows = merge_financial_rows(key_metric_rows, llm_rows)

    payload["financial_table"] = merged_rows

    completeness = 0.0
    if merged_rows:
        filled_cells = 0
        total_cells = len(merged_rows) * 4
        for row in merged_rows:
            for field in ("revenue", "ebitda", "pat", "ebitda_margin"):
                if str(row.get(field, "")).strip():
                    filled_cells += 1
        if total_cells:
            completeness = round(filled_cells / total_cells, 2)

    payload["table_quality"] = {
        "parser_rows": len(parser_rows),
        "llm_rows": len(llm_rows),
        "merged_rows": len(merged_rows),
        "completeness": completeness,
    }
    return payload
