"""Embed chunk records and upload them to the Azure AI Search index."""

import argparse
import json
import os
from collections.abc import Iterator
from datetime import datetime
from itertools import islice
from pathlib import Path
from time import monotonic

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv
from openai import OpenAI


INPUT_FILE = Path("data/chunks.jsonl")
EMBEDDING_BATCH_SIZE = 64
UPLOAD_BATCH_SIZE = 500
PROGRESS_INTERVAL_SECONDS = 5 * 60


def read_chunks(input_file: Path) -> Iterator[dict]:
    """Yield non-empty JSON Lines records from an extracted chunk file."""
    with input_file.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number} of {input_file}."
                ) from error


def batches(records: Iterator[dict], batch_size: int) -> Iterator[list[dict]]:
    """Yield records in fixed-size batches."""
    while batch := list(islice(records, batch_size)):
        yield batch


def count_chunks(input_file: Path, limit: int | None) -> int:
    """Count non-empty records, respecting an optional upload limit."""
    with input_file.open(encoding="utf-8") as file:
        chunk_count = sum(1 for line in file if line.strip())
    return min(chunk_count, limit) if limit is not None else chunk_count


def build_search_documents(
    records: list[dict], embeddings: list[list[float]]
) -> list[dict]:
    """Map chunk records and embeddings to the Azure AI Search index schema."""
    return [
        {
            "id": record["id"],
            "content": record["text"],
            "source_document": record["source_document"],
            "chunk_index": record["chunk_index"],
            "character_start": record["character_start"],
            "character_end": record["character_end"],
            "content_vector": embedding,
        }
        for record, embedding in zip(records, embeddings, strict=True)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create embeddings and upload chunks to Azure AI Search."
    )
    parser.add_argument("--input-file", type=Path, default=INPUT_FILE)
    parser.add_argument(
        "--limit",
        type=int,
        help="Upload only this many chunks; useful for a smoke test.",
    )
    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be at least 1.")
    if not args.input_file.is_file():
        raise SystemExit(f"Chunk file not found: {args.input_file}")

    total_chunks = count_chunks(args.input_file, args.limit)
    load_dotenv()
    openai_client = OpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        base_url=os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/",
    )
    search_client = SearchClient(
        endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
        index_name=os.environ["AZURE_SEARCH_INDEX_NAME"],
        credential=AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"]),
    )
    deployment = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]

    chunk_records = read_chunks(args.input_file)
    if args.limit is not None:
        chunk_records = islice(chunk_records, args.limit)

    print(f"Starting upload of {total_chunks} chunk(s).", flush=True)
    started_at = monotonic()
    last_progress_at = started_at
    processed_count = 0
    uploaded_count = 0
    pending_documents: list[dict] = []
    for record_batch in batches(chunk_records, EMBEDDING_BATCH_SIZE):
        response = openai_client.embeddings.create(
            model=deployment,
            input=[record["text"] for record in record_batch],
        )
        processed_count += len(record_batch)
        print(".", end="", flush=True)
        pending_documents.extend(
            build_search_documents(
                record_batch, [item.embedding for item in response.data]
            )
        )

        now = monotonic()
        if now - last_progress_at >= PROGRESS_INTERVAL_SECONDS:
            elapsed_minutes = (now - started_at) / 60
            timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
            print(
                f"\n[{timestamp}] Processed {processed_count:,} of "
                f"{total_chunks:,} chunk(s) in {elapsed_minutes:.1f} minutes.",
                flush=True,
            )
            last_progress_at = now

        while len(pending_documents) >= UPLOAD_BATCH_SIZE:
            results = search_client.upload_documents(
                documents=pending_documents[:UPLOAD_BATCH_SIZE]
            )
            failures = [result for result in results if not result.succeeded]
            if failures:
                raise RuntimeError(f"Failed to upload {len(failures)} document(s).")
            uploaded_count += len(results)
            del pending_documents[:UPLOAD_BATCH_SIZE]

    if pending_documents:
        results = search_client.upload_documents(documents=pending_documents)
        failures = [result for result in results if not result.succeeded]
        if failures:
            raise RuntimeError(f"Failed to upload {len(failures)} document(s).")
        uploaded_count += len(results)

    if processed_count:
        print()
    print(f"Uploaded {uploaded_count} chunk(s) to Azure AI Search.")


if __name__ == "__main__":
    main()