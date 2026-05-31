from __future__ import annotations

import json
import re
from datetime import date
from typing import Any


def today_label() -> str:
    return date.today().strftime("%d %B %Y")


def extract_json_object(text: str) -> dict[str, Any]:
    """Try hard to extract a JSON object from model output."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {}

    candidate = match.group(0)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return {}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def normalize_confidence(value: Any) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, out))


def normalize_metric_value(value: Any) -> str:
    return clean_text(value)


def first_non_empty(*values: Any) -> str:
    for value in values:
        cleaned = clean_text(value)
        if cleaned:
            return cleaned
    return ""
