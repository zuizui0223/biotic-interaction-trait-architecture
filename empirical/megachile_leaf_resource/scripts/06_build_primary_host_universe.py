#!/usr/bin/env python3
"""Build the evidence-backed primary plant universe from validated ledger rows."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
from trait_architecture.host_evidence import primary_host_universe  # noqa: E402

OUTPUT_FIELDS = (
    "plant_name_accepted",
    "number_of_direct_records",
    "number_of_bee_species",
    "bee_species",
    "supporting_source_count",
    "supporting_source_ids",
    "evidence_grade_best",
    "Japan_record_count",
    "trait_coverage_status",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Reviewed ledger or validation output")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    universe = primary_host_universe(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(universe)
    print(f"wrote {len(universe)} primary host plant taxa to {args.output}")


if __name__ == "__main__":
    main()
