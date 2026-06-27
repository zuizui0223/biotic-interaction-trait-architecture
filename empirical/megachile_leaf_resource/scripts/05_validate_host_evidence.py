#!/usr/bin/env python3
"""Validate reviewed host-evidence rows without silently changing them."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
from trait_architecture.host_evidence import validate_host_evidence_record  # noqa: E402


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fail-on-errors", action="store_true")
    args = parser.parse_args()

    fields, rows = read_rows(args.input)
    output_rows: list[dict[str, str]] = []
    error_count = 0
    for row in rows:
        errors, warnings = validate_host_evidence_record(row)
        error_count += bool(errors)
        enriched = dict(row)
        enriched["validation_status"] = "error" if errors else ("warning" if warnings else "valid")
        enriched["validation_errors"] = " | ".join(errors)
        enriched["validation_warnings"] = " | ".join(warnings)
        output_rows.append(enriched)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_fields = fields + ["validation_status", "validation_errors", "validation_warnings"]
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"validated {len(rows)} records; {error_count} rows have fatal errors")
    if args.fail_on_errors and error_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
