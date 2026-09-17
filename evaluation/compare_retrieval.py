"""Compare vector and hybrid retrieval across configured retrieval depths."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.run_evaluation import normalize_path
from rag.ask import retrieve_sources


DEFAULT_QUESTIONS_FILE = Path("evaluation/questions.json")
DEFAULT_OUTPUT_FILE = Path("evaluation/retrieval_comparison.json")
RETRIEVAL_MODES = ("vector", "hybrid")
TOP_VALUES = (3, 5, 8)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare retrieval modes and depths against expected sources."
    )
    parser.add_argument("--questions-file", type=Path, default=DEFAULT_QUESTIONS_FILE)
    parser.add_argument("--output-file", type=Path, default=DEFAULT_OUTPUT_FILE)
    args = parser.parse_args()

    if not args.questions_file.is_file():
        raise SystemExit(f"Question file not found: {args.questions_file}")
    questions = json.loads(args.questions_file.read_text(encoding="utf-8"))
    comparisons = []

    for retrieval_mode in RETRIEVAL_MODES:
        for top in TOP_VALUES:
            print(f"Evaluating {retrieval_mode} retrieval with top={top}", flush=True)
            result_rows = []
            for question in questions:
                sources = retrieve_sources(question["question"], top, retrieval_mode)
                retrieved_sources = [source["source_document"] for source in sources]
                expected_source = normalize_path(question["expected_source_document"])
                expected_source_retrieved = expected_source in {
                    normalize_path(source) for source in retrieved_sources
                }
                result_rows.append(
                    {
                        "id": question["id"],
                        "expected_source_retrieved": expected_source_retrieved,
                        "retrieved_sources": retrieved_sources,
                    }
                )

            hits = sum(row["expected_source_retrieved"] for row in result_rows)
            comparisons.append(
                {
                    "retrieval_mode": retrieval_mode,
                    "top": top,
                    "expected_source_retrieval_hits": hits,
                    "expected_source_retrieval_rate": hits / len(questions),
                    "results": result_rows,
                }
            )

    report = {
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "question_count": len(questions),
        "comparisons": comparisons,
    }
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.output_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    for comparison in comparisons:
        print(
            f"{comparison['retrieval_mode']} top={comparison['top']}: "
            f"{comparison['expected_source_retrieval_hits']} of {len(questions)} "
            "expected sources retrieved."
        )
    print(f"Results written to: {args.output_file}")


if __name__ == "__main__":
    main()