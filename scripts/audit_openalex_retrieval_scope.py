"""Audit current OpenAlex depth for the historical and omitted query routes.

Usage:
    python scripts/audit_openalex_retrieval_scope.py \
      empirical/matched_flower_regime/literature_seed_queries.csv \
      artifacts/openalex_retrieval_scope
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

from trait_architecture.openalex_retrieval_scope_audit import run_scope_audit, write_scope_audit


def read_queries(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = [{key: str(value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]
    if not rows:
        raise ValueError("query registry is empty")
    return rows


def write_failure_receipt(out_dir: Path, error: Exception) -> None:
    """Persist diagnostic metadata without storing a key or a partial candidate result."""

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "openalex_scope_failure.json").write_text(
        json.dumps(
            {
                "status": "failed",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "openalex_api_key_configured": bool(os.environ.get("OPENALEX_API_KEY", "").strip()),
                "interpretation_boundary": (
                    "This receipt records a failed retrieval attempt only. It does not imply zero candidates, "
                    "zero expansion potential, or a completed scope audit."
                ),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query_registry")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)

    try:
        _, candidates, report = run_scope_audit(read_queries(args.query_registry))
    except Exception as error:
        write_failure_receipt(out_dir, error)
        raise
    write_scope_audit(out_dir, candidates, report)
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
