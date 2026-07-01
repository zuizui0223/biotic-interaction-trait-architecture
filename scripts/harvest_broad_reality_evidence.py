"""Retrieve a high-recall Crossref corpus for broad real-world evidence checks.

Usage:
    python scripts/harvest_broad_reality_evidence.py \
      empirical/broad_reality_evidence/broad_evidence_query_registry.csv \
      artifacts/broad_reality_evidence \
      --rows-per-query 200
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from trait_architecture.broad_reality_evidence import (
    ROWS_PER_QUERY_DEFAULT,
    harvest_crossref,
    read_query_registry,
    summary,
    write_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query_registry")
    parser.add_argument("out_dir")
    parser.add_argument("--rows-per-query", type=int, default=ROWS_PER_QUERY_DEFAULT)
    args = parser.parse_args(argv)

    queries = read_query_registry(args.query_registry)
    candidates, reports = harvest_crossref(queries, rows_per_query=args.rows_per_query)
    write_outputs(Path(args.out_dir), candidates, reports)
    print(json.dumps(summary(candidates, reports), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
