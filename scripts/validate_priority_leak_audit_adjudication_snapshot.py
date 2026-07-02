"""Validate that the registered abstract audit overlay reproduces its snapshot.

Usage:
  python scripts/validate_priority_leak_audit_adjudication_snapshot.py \
    PACKET.csv OVERRIDES.csv EXPECTED_YIELD.csv EXPECTED_COMPARISONS.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from trait_architecture.priority_leak_audit_adjudication import read, summarize
from trait_architecture.priority_leak_audit_overlay import materialize_abstract_adjudication, read_overlay


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet_csv")
    parser.add_argument("overrides_csv")
    parser.add_argument("expected_yield_csv")
    parser.add_argument("expected_comparisons_csv")
    args = parser.parse_args(argv)

    sheet = materialize_abstract_adjudication(read(args.packet_csv), read_overlay(args.overrides_csv))
    summary, comparisons, _ = summarize(sheet)
    expected_summary = read_csv(args.expected_yield_csv)
    expected_comparisons = read_csv(args.expected_comparisons_csv)
    if summary != expected_summary:
        raise SystemExit("registered route-group yield snapshot does not match regenerated audit")
    if comparisons != expected_comparisons:
        raise SystemExit("registered route-comparison snapshot does not match regenerated audit")
    print(f"validated_adjudication_rows={len(sheet)} route_groups={len(summary)} comparisons={len(comparisons)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
