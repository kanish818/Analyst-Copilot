from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from pypdf import PdfReader


@dataclass
class IngestedDocument:
    name: str
    kind: str
    text: str


@dataclass
class IngestResult:
    combined_text: str
    documents: list[IngestedDocument]


def _pdf_to_text(name: str, data: bytes) -> IngestedDocument:
    reader = PdfReader(io.BytesIO(data))
    chunks: list[str] = []
    for idx, page in enumerate(reader.pages, start=1):
        page_text = (page.extract_text() or "").strip()
        if page_text:
            chunks.append(f"[PAGE {idx}] {page_text}")
    text = "\n\n".join(chunks)
    return IngestedDocument(name=name, kind="pdf", text=text)


def _csv_to_text(name: str, data: bytes) -> IngestedDocument:
    df = pd.read_csv(io.BytesIO(data))
    preview = df.head(30).fillna("")
    text = "\n".join(
        [
            f"[CSV FILE: {name}]",
            "Columns: " + ", ".join(map(str, preview.columns.tolist())),
            preview.to_csv(index=False),
        ]
    )
    return IngestedDocument(name=name, kind="csv", text=text)


def _txt_to_text(name: str, data: bytes) -> IngestedDocument:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1", errors="ignore")
    return IngestedDocument(name=name, kind="txt", text=text)


def _as_name(uploaded_file: Any) -> str:
    if hasattr(uploaded_file, "name"):
        return str(uploaded_file.name)
    return "document"


def _as_bytes(uploaded_file: Any) -> bytes:
    if hasattr(uploaded_file, "getvalue"):
        return bytes(uploaded_file.getvalue())
    if isinstance(uploaded_file, (bytes, bytearray)):
        return bytes(uploaded_file)
    raise ValueError("Unsupported uploaded file type")


def ingest_uploaded_files(uploaded_files: list[Any]) -> IngestResult:
    documents: list[IngestedDocument] = []

    for uploaded_file in uploaded_files:
        name = _as_name(uploaded_file)
        data = _as_bytes(uploaded_file)
        ext = Path(name).suffix.lower()

        if ext == ".pdf":
            doc = _pdf_to_text(name, data)
        elif ext == ".csv":
            doc = _csv_to_text(name, data)
        elif ext in {".txt", ".md"}:
            doc = _txt_to_text(name, data)
        else:
            # Fallback: attempt text decode for unknown text-like files.
            doc = _txt_to_text(name, data)

        documents.append(doc)

    combined = "\n\n".join(f"[SOURCE: {d.name}]\n{d.text}" for d in documents)
    return IngestResult(combined_text=combined, documents=documents)
