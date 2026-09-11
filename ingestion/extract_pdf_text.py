"""Extract text from PDF documents into local, untracked output files."""

import argparse
import json
from pathlib import Path

from pypdf import PdfReader


def extract_pdf(pdf_path: Path, output_path: Path) -> dict:
    try:
        reader = PdfReader(pdf_path)
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(pages).strip()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")

        return {
            "source": str(pdf_path),
            "status": "success",
            "page_count": len(reader.pages),
            "characters_extracted": len(text),
            "output": str(output_path),
        }
    except Exception as error:
        return {
            "source": str(pdf_path),
            "status": "failed",
            "error": str(error),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract text from PDF files.")
    parser.add_argument("source_directory", type=Path)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("data/extracted_text"),
    )
    args = parser.parse_args()

    source_directory = args.source_directory.resolve()
    output_directory = args.output_directory

    if not source_directory.is_dir():
        raise SystemExit(f"Directory not found: {source_directory}")

    pdf_files = sorted(source_directory.rglob("*.pdf"))
    results = []

    for pdf_path in pdf_files:
        relative_path = pdf_path.relative_to(source_directory)
        text_path = output_directory / relative_path.with_suffix(".txt")

        print(f"Extracting: {relative_path}")
        results.append(extract_pdf(pdf_path, text_path))

    report_path = Path("data/extraction_report.json")
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    successful = sum(result["status"] == "success" for result in results)
    print(f"\nExtracted {successful} of {len(results)} PDF file(s).")
    print(f"Report written to: {report_path}")


if __name__ == "__main__":
    main() 