"""
ingest.py — Convert all PDFs and CSVs in documents/ to .txt files.

PDFs: extract text page by page using pdfplumber.
CSVs: write each row as a tab-separated line so structure is preserved.
Output .txt files are saved alongside the originals in documents/.
"""

import csv
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    sys.exit("pdfplumber not installed. Run: pip install pdfplumber==0.11.4")

DOCUMENTS_DIR = Path(__file__).parent / "documents"


def pdf_to_txt(pdf_path: Path) -> None:
    out_path = pdf_path.with_suffix(".txt")
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append(f"--- Page {i} ---\n{text}")
    out_path.write_text("\n\n".join(pages), encoding="utf-8")
    print(f"  PDF  {pdf_path.name} → {out_path.name}  ({len(pages)} pages)")


def csv_to_txt(csv_path: Path) -> None:
    out_path = csv_path.with_suffix(".txt")
    lines = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            lines.append("\t".join(row))
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  CSV  {csv_path.name} → {out_path.name}  ({len(lines)} rows)")


def main() -> None:
    pdfs = sorted(DOCUMENTS_DIR.glob("*.pdf"))
    csvs = sorted(DOCUMENTS_DIR.glob("*.csv"))

    if not pdfs and not csvs:
        print("No PDF or CSV files found in documents/")
        return

    print(f"Found {len(pdfs)} PDF(s) and {len(csvs)} CSV(s) in {DOCUMENTS_DIR}\n")

    for pdf in pdfs:
        pdf_to_txt(pdf)

    for csv_file in csvs:
        csv_to_txt(csv_file)

    print("\nDone. All files converted to .txt")


if __name__ == "__main__":
    main()
