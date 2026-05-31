from __future__ import annotations

import re
from typing import Any


PERIOD_PATTERN = re.compile(r"\b(Q[1-4]\s*FY\s*\d{2})\b", flags=re.IGNORECASE)
NUMBER_PATTERN = r"([0-9][0-9,]*\.?[0-9]*)"


def _normalize_period(raw: str) -> str:
    compact = re.sub(r"\s+", "", raw.upper())
    return compact.replace("FY", "FY")


def _clean_value(raw: str) -> str:
    return raw.replace(",", "").strip()


def _extract_metric_value(line: str, metric: str) -> str:
    patterns = {
        "revenue": rf"(?:revenue|total income|income|net interest income)[^0-9₹rs]{{0,35}}(?:₹|rs\.?\s*)?{NUMBER_PATTERN}\s*(?:crore|cr|million|mn|bn)?",
        "ebitda": rf"(?:ebitda|operating profit|profit before tax|pbt)[^0-9₹rs]{{0,35}}(?:₹|rs\.?\s*)?{NUMBER_PATTERN}\s*(?:crore|cr|million|mn|bn)?",
        "pat": rf"(?:\bpat\b|net profit|profit after tax)[^0-9₹rs]{{0,35}}(?:₹|rs\.?\s*)?{NUMBER_PATTERN}\s*(?:crore|cr|million|mn|bn)?",
        "ebitda_margin": rf"(?:ebitda margin|ebit margin)[^0-9]{{0,20}}{NUMBER_PATTERN}\s*%",
    }
    match = re.search(patterns[metric], line, flags=re.IGNORECASE)
    if not match:
        return ""
    return _clean_value(match.group(1))


def _extract_period_rows_from_lines(context_text: str) -> list[dict[str, str]]:
    rows_by_period: dict[str, dict[str, str]] = {}
    lines = [line.strip() for line in re.split(r"[\r\n]+", context_text) if line.strip()]
    active_period = ""

    for line in lines:
        period_match = PERIOD_PATTERN.search(line)
        if period_match:
            active_period = _normalize_period(period_match.group(1))
        if not active_period:
            continue
        period = active_period
        row = rows_by_period.setdefault(
            period,
            {
                "period": period,
                "revenue": "",
                "ebitda": "",
                "pat": "",
                "ebitda_margin": "",
                "source": "parser",
                "source_page": "",
            },
        )

        for metric in ("revenue", "ebitda", "pat", "ebitda_margin"):
            if row[metric]:
                continue
            value = _extract_metric_value(line, metric)
            if value:
                row[metric] = value

        page_match = re.search(r"\[PAGE\s+(\d+)\]", line, flags=re.IGNORECASE)
        if page_match:
            row["source_page"] = f"PAGE {page_match.group(1)}"

    return list(rows_by_period.values())


def _fill_single_latest_row_from_text(context_text: str) -> list[dict[str, str]]:
    period_match = PERIOD_PATTERN.search(context_text)
    period = _normalize_period(period_match.group(1)) if period_match else "LATEST"
    row = {
        "period": period,
        "revenue": _extract_metric_value(context_text, "revenue"),
        "ebitda": _extract_metric_value(context_text, "ebitda"),
        "pat": _extract_metric_value(context_text, "pat"),
        "ebitda_margin": _extract_metric_value(context_text, "ebitda_margin"),
        "source": "parser",
        "source_page": "",
    }
    if any(row[key] for key in ("revenue", "ebitda", "pat", "ebitda_margin")):
        return [row]
    return []


def parse_financial_rows_from_text(context_text: str) -> list[dict[str, str]]:
    rows = _extract_period_rows_from_lines(context_text)
    rows = [
        row
        for row in rows
        if any(row.get(field, "").strip() for field in ("revenue", "ebitda", "pat", "ebitda_margin"))
    ]
    if rows:
        return rows
    return _fill_single_latest_row_from_text(context_text)


def _sanitize_row(row: dict[str, Any], source_default: str) -> dict[str, str]:
    return {
        "period": str(row.get("period", "")).strip().upper().replace(" ", ""),
        "revenue": str(row.get("revenue", "")).strip(),
        "ebitda": str(row.get("ebitda", "")).strip(),
        "pat": str(row.get("pat", "")).strip(),
        "ebitda_margin": str(row.get("ebitda_margin", "")).strip(),
        "source": str(row.get("source", source_default)).strip() or source_default,
        "source_page": str(row.get("source_page", "")).strip(),
    }


def merge_financial_rows(
    parser_rows: list[dict[str, Any]],
    llm_rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}

    for row in parser_rows:
        normalized = _sanitize_row(row, "parser")
        if not normalized["period"]:
            continue
        merged[normalized["period"]] = normalized

    for row in llm_rows:
        normalized = _sanitize_row(row, "llm")
        period = normalized["period"]
        if not period:
            continue
        current = merged.get(period)
        if not current:
            merged[period] = normalized
            continue
        for field in ("revenue", "ebitda", "pat", "ebitda_margin", "source_page"):
            if not current[field] and normalized[field]:
                current[field] = normalized[field]
        if current["source"] != "parser" and normalized["source"] == "llm":
            current["source"] = "llm"

    return sorted(merged.values(), key=lambda item: item["period"])


def derive_row_from_key_metrics(key_metrics: list[dict[str, Any]], context_text: str) -> list[dict[str, str]]:
    period_match = PERIOD_PATTERN.search(context_text)
    period = _normalize_period(period_match.group(1)) if period_match else "LATEST"
    row = {
        "period": period,
        "revenue": "",
        "ebitda": "",
        "pat": "",
        "ebitda_margin": "",
        "source": "key_metrics",
        "source_page": "",
    }

    for metric in key_metrics:
        name = str(metric.get("name", "")).lower()
        value = str(metric.get("value", "")).strip()
        if not value:
            continue
        if "revenue" in name and not row["revenue"]:
            row["revenue"] = value
        elif "ebitda" in name and "margin" not in name and not row["ebitda"]:
            row["ebitda"] = value
        elif ("pat" in name or "net profit" in name) and not row["pat"]:
            row["pat"] = value
        elif "margin" in name and not row["ebitda_margin"]:
            row["ebitda_margin"] = value

    if any(row[key] for key in ("revenue", "ebitda", "pat", "ebitda_margin")):
        return [row]
    return []
