from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from services.pipeline import AnalystCopilotPipeline


@dataclass
class LocalUpload:
    path: Path

    @property
    def name(self) -> str:
        return self.path.name

    def getvalue(self) -> bytes:
        return self.path.read_bytes()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    pipeline = AnalystCopilotPipeline(root)

    scenarios = [
        ("L&T Technology Services", [root / "LTTS Q2FY26.pdf"]),
        ("Pondy Oxides and Chemicals", [root / "POCL Q2FY26.pdf"]),
        (
            "Tata Motors",
            [root / "data" / "external" / "Tata_Motors_Integrated_Annual_Report_2024_25.pdf"],
        ),
    ]

    output_dir = root / "examples"
    output_dir.mkdir(parents=True, exist_ok=True)

    for company_name, docs in scenarios:
        uploads = [LocalUpload(path=doc) for doc in docs if doc.exists()]
        if not uploads:
            continue

        report, pdf_bytes = pipeline.run(company_name, uploads)
        out_file = output_dir / f"{company_name.replace(' ', '_')}_analyst_report.pdf"
        out_file.write_bytes(pdf_bytes)
        print(f"Generated: {out_file}")
        json_file = output_dir / f"{company_name.replace(' ', '_')}_extraction.json"
        json_file.write_text(
            json.dumps(report.raw_extraction, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
