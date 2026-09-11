"""Split extracted text into overlapping chunks with source metadata."""

import hashlib
import json
from pathlib import Path


INPUT_DIRECTORY = Path("data/extracted_text")
OUTPUT_FILE = Path("data/chunks.jsonl")
REPORT_FILE = Path("data/chunking_report.json")

CHUNK_SIZE = 1_200       # characters; a practical first baseline
CHUNK_OVERLAP = 200      # keeps context between adjacent chunks


def split_text(text: str) -> list[tuple[int, int, str]]:
    """Return chunks as (start_offset, end_offset, text)."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + CHUNK_SIZE, text_length)

        if end < text_length:
            boundary = text.rfind(" ", start, end)
            if boundary > start + (CHUNK_SIZE // 2):
                end = boundary

        chunk = text[start:end].strip()

        if chunk:
            chunks.append((start, end, chunk))

        if end >= text_length:
            break

        start = max(end - CHUNK_OVERLAP, start + 1)

        while start < text_length and text[start].isspace():
            start += 1

    return chunks


def main() -> None:
    if not INPUT_DIRECTORY.is_dir():
        raise SystemExit(f"Input directory not found: {INPUT_DIRECTORY}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    document_count = 0
    chunk_count = 0

    with OUTPUT_FILE.open("w", encoding="utf-8") as output_file:
        for text_path in sorted(INPUT_DIRECTORY.rglob("*.txt")):
            relative_text_path = text_path.relative_to(INPUT_DIRECTORY)
            source_pdf_path = relative_text_path.with_suffix(".pdf")
            text = text_path.read_text(encoding="utf-8")

            if not text.strip():
                continue

            document_count += 1

            for chunk_index, (start, end, chunk_text) in enumerate(split_text(text)):
                chunk_id_source = (
                    f"{source_pdf_path}|{chunk_index}|{start}|{end}"
                )
                chunk_id = hashlib.sha256(
                    chunk_id_source.encode("utf-8")
                ).hexdigest()

                record = {
                    "id": chunk_id,
                    "source_document": str(source_pdf_path),
                    "chunk_index": chunk_index,
                    "character_start": start,
                    "character_end": end,
                    "text": chunk_text,
                }

                output_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                chunk_count += 1

    report = {
        "documents_chunked": document_count,
        "chunks_created": chunk_count,
        "chunk_size_characters": CHUNK_SIZE,
        "chunk_overlap_characters": CHUNK_OVERLAP,
    }

    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Chunked {document_count} document(s).")
    print(f"Created {chunk_count} chunk(s).")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main() 