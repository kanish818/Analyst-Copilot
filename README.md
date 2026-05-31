# Analyst Copilot (Bull AI Assessment)

A minimal but modular web app that converts a company financial context document into a Geojit-style downloadable research PDF.

## What makes this submission unique

- Analyst-Copilot layer: each extracted metric includes confidence, source excerpt/page, and assumption notes.
- Data quality panel in UI: extracted metric count, low-confidence flags, missing narrative sections.
- Graceful fallback extraction when model output is incomplete.

## Tech Stack

- Python 3.11+
- Streamlit (UI)
- Groq LLM API (OpenAI-compatible)
- pypdf + pandas (ingestion)
- reportlab + matplotlib (PDF and charts)

## Project Structure

- `app/main.py`: Streamlit app entry point
- `app/services/ingest.py`: PDF/CSV/TXT ingestion
- `app/services/extractor.py`: LLM extraction + fallback
- `app/services/mapper.py`: payload to normalized report model
- `app/services/pdf_report.py`: Geojit-style report rendering
- `app/services/charts.py`: chart generation
- `app/services/pipeline.py`: end-to-end orchestration
- `app/generate_examples.py`: generate sample outputs from provided docs
- `tests/test_mapper.py`: normalization unit test

## Template Field Definition

Template fields are defined in the extraction schema prompt and normalized model:

- Schema prompt: `app/services/extractor.py` (`SYSTEM_PROMPT`)
- Typed report objects: `app/services/models.py`
- Mapping logic: `app/services/mapper.py`

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Environment

Create `.env` from `.env.example` and set:

```env
GROQ_API_KEY=your_key
GROQ_MODEL=llama-3.3-70b-versatile
```

## Run UI

```bash
streamlit run app/main.py
```

UI Inputs:
- Company name
- Upload one or more context files (`.pdf`, `.csv`, `.txt`)

UI Output:
- One-click PDF download
- Metric confidence + citation table

## Generate Example Outputs

```bash
python app/generate_examples.py
```

This generates PDFs in `examples/`.

## Included Demo Documents

Provided assessment docs:
- `LTTS Q2FY26.pdf`
- `POCL Q2FY26.pdf`
- `ICICI Q2FY26.pdf`
- `JSW Energy Q2FY26.pdf`
- `Eternal-Geojit.pdf`

Extra external annual report for stronger demo:
- `data/external/Tata_Motors_Integrated_Annual_Report_2024_25.pdf`

## Acceptance Criteria Mapping

- Geojit-like report layout and section flow: implemented in `pdf_report.py`
- Financial tables + narrative + chart: generated in report pipeline
- Multiple input formats: PDF/CSV/TXT supported
- Missing fields handled gracefully: defaults and placeholders in mapper/PDF renderer
- One-click download: Streamlit `download_button`

## Notes

- If the LLM fails or key is missing, heuristic extraction still creates a usable draft report.
- For best results, include investor presentation PDFs with explicit metric statements.

## Repository

GitHub target: [kanish818/Analyst-Copilot](https://github.com/kanish818/Analyst-Copilot)
