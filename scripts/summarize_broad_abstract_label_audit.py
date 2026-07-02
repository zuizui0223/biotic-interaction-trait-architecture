"""Summarize a completed broad-abstract human coding sheet.

Usage:
    python scripts/summarize_broad_abstract_label_audit.py \
      broad_abstract_label_audit_coding_sheet.csv \
      broad_abstract_label_audit_design.csv \
      artifacts/broad_abstract_label_audit_summary

The command produces calibration outputs only after the selected audit rows have
been coded as reviewed. It does not retrieve papers or alter the fixed corpus.
"""

from __future__ import annotations

import argparse

from trait_architecture.broad_abstract_label_audit import (
    CODING_FIELDS,
    DESIGN_FIELDS,
    read_rows,
    summarize_audit,
    write_audit_summary,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("coding_sheet_csv")
    parser.add_argument("design_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)

    completion, precision, coverage, control = summarize_audit(
        read_rows(args.coding_sheet_csv, CODING_FIELDS),
        read_rows(args.design_csv, DESIGN_FIELDS),
    )
    write_audit_summary(args.out_dir, completion, precision, coverage, control)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
