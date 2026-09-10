"""Create an inventory of source documents without copying them."""

import argparse
import json
from datetime import datetime
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf"}


def build_inventory(source_directory: Path) -> list[dict]:
    documents = []

    for file_path in sorted(source_directory.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        stat = file_path.stat()
        documents.append(
            {
                "file_name": file_path.name,
                "relative_path": str(file_path.relative_to(source_directory)),
                "extension": file_path.suffix.lower(),
                "size_bytes": stat.st_size,
                "modified_utc": datetime.fromtimestamp(
                    stat.st_mtime
                ).isoformat(timespec="seconds"),
            }
        )

    return documents


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a JSON inventory of supported source documents."
    )
    parser.add_argument("source_directory", type=Path)
    args = parser.parse_args()

    source_directory = args.source_directory.resolve()

    if not source_directory.is_dir():
        raise SystemExit(f"Directory not found: {source_directory}")

    inventory = build_inventory(source_directory)

    output_directory = Path("data")
    output_directory.mkdir(exist_ok=True)
    output_path = output_directory / "inventory.json"

    output_path.write_text(
        json.dumps(
            {
                "source_directory": str(source_directory),
                "document_count": len(inventory),
                "documents": inventory,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Found {len(inventory)} supported document(s).")
    print(f"Inventory written to: {output_path}")


if __name__ == "__main__":
    main()