"""Build a blank source-screening matrix from a broad priority cohort.

Usage:
    python scripts/build_broad_source_screening_matrix.py \
      artifacts/broad_reality_evidence/broad_reality_evidence_priority.csv \
      artifacts/broad_reality_evidence/broad_source_screening_matrix.csv
"""

from __future__ import annotations

import argparse

from trait_architecture.broad_source_screening import (
    initial_source_screening_matrix,
    read_priority_candidates,
    write_source_screening_matrix,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("priority_csv")
    parser.add_argument("output_csv")
    args = parser.parse_args(argv)

    matrix = initial_source_screening_matrix(read_priority_candidates(args.priority_csv))
    write_source_screening_matrix(args.output_csv, matrix)
    print(f"source_screening_rows={len(matrix)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
