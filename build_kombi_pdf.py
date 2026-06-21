from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfWriter


ROOT = Path(__file__).resolve().parent
PAPER_DIR = ROOT / "paper"
BASE = "Review_Multiaxiale_Diagnostik"


def build(version: str) -> Path:
    en_pdf = PAPER_DIR / f"{BASE}_{version}_en.pdf"
    ger_pdf = PAPER_DIR / f"{BASE}_{version}_ger.pdf"
    out_pdf = PAPER_DIR / f"{BASE}_{version}_kombi.pdf"

    for pdf in (en_pdf, ger_pdf):
        if not pdf.exists():
            raise FileNotFoundError(f"Missing input PDF: {pdf}")

    writer = PdfWriter()
    writer.append(str(en_pdf), import_outline=False)
    writer.append(str(ger_pdf), import_outline=False)
    writer.add_metadata(
        {
            "/Title": (
                "An Integrated Multiaxial Model for Computer-Assisted Psychiatric Diagnosis / "
                "Ein integriertes multiaxiales Modell zur computergestützten psychiatrischen "
                "Diagnostik (EN+DE)"
            ),
            "/Author": "Lukas Geiger",
            "/Subject": (
                "Combined bilingual methods and design paper for a 6-axis psychiatric "
                "decision support system"
            ),
            "/Keywords": (
                "multiaxial diagnosis, multiaxiale Diagnostik, psychiatric decision support, "
                "Entscheidungsunterstützung, DSM-5-TR, ICD-11, ICF, coverage analysis, "
                "Abdeckungsanalyse"
            ),
        }
    )

    with out_pdf.open("wb") as handle:
        writer.write(handle)

    return out_pdf


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v4")
    args = parser.parse_args()
    print(build(args.version))


if __name__ == "__main__":
    main()
