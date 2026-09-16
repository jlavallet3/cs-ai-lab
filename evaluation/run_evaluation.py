"""Evaluate RAG retrieval and answers against the project question set."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.ask import ask_question


DEFAULT_QUESTIONS_FILE = Path("evaluation/questions.json")
DEFAULT_OUTPUT_FILE = Path("evaluation/results.json")


def normalize_path(path: str) -> str:
    """Normalize source paths before comparing them across operating systems."""
    return path.replace("\\", "/")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate retrieval against the CS AI Lab question set."
    )
    parser.add_argument("--questions-file", type=Path, default=DEFAULT_QUESTIONS_FILE)
    parser.add_argument("--output-file", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--limit", type=int, help="Evaluate only this many questions.")
    args = parser.parse_args()

    if args.top < 1:
        raise SystemExit("--top must be at least 1.")
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be at least 1.")
    if not args.questions_file.is_file():
        raise SystemExit(f"Question file not found: {args.questions_file}")

    questions = json.loads(args.questions_file.read_text(encoding="utf-8"))
    if args.limit is not None:
        questions = questions[:args.limit]

    results = []
    for position, question in enumerate(questions, start=1):
        print(f"Evaluating {position} of {len(questions)}: {question['id']}", flush=True)
        try:
            answer, sources = ask_question(question["question"], args.top)
            retrieved_sources = [source["source_document"] for source in sources]
            expected_source = normalize_path(question["expected_source_document"])
            expected_source_retrieved = expected_source in {
                normalize_path(source) for source in retrieved_sources
            }
            results.append(
                {
                    "id": question["id"],
                    "question": question["question"],
                    "expected_source_document": question["expected_source_document"],
                    "expected_source_retrieved": expected_source_retrieved,
                    "retrieved_sources": retrieved_sources,
                    "answer": answer,
                }
            )
        except Exception as error:
            results.append(
                {
                    "id": question["id"],
                    "question": question["question"],
                    "expected_source_document": question["expected_source_document"],
                    "error": str(error),
                }
            )

    successful_results = [result for result in results if "error" not in result]
    expected_source_hits = sum(
        result["expected_source_retrieved"] for result in successful_results
    )
    report = {
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "question_count": len(results),
        "successful_question_count": len(successful_results),
        "expected_source_retrieval_hits": expected_source_hits,
        "expected_source_retrieval_rate": (
            expected_source_hits / len(successful_results)
            if successful_results
            else 0
        ),
        "results": results,
    }
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.output_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        f"Expected source retrieved for {expected_source_hits} of "
        f"{len(successful_results)} successful question(s)."
    )
    print(f"Results written to: {args.output_file}")


if __name__ == "__main__":
    main()