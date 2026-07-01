"""Create the route-balanced calibration batch from one pinned priority cohort.

Usage:
    python scripts/build_broad_calibration_batch.py \
      artifacts/broad_reality_evidence/broad_reality_evidence_priority.csv \
      artifacts/broad_reality_evidence/broad_calibration_batch.csv \
      --per-route 10
"""

from __future__ import annotations

import argparse

from trait_architecture.broad_calibration_batch import (
    select_calibration_batch,
    write_calibration_batch,
)
from trait_architecture.broad_source_screening import read_priority_candidates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("priority_csv")
    parser.add_argument("output_csv")
    parser.add_argument("--per-route", type=int, default=10)
    args = parser.parse_args(argv)

    batch = select_calibration_batch(read_priority_candidates(args.priority_csv), per_route=args.per_route)
    write_calibration_batch(args.output_csv, batch)
    print(f"calibration_batch_rows={len(batch)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
