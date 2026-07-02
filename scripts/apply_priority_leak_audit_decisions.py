"""Materialize the registered abstract-level priority-leak audit adjudication.

Usage:
  python scripts/apply_priority_leak_audit_decisions.py PACKET.csv OVERRIDES.csv OUTPUT_SHEET.csv OUTPUT_DIR
"""

from __future__ import annotations

import argparse

from trait_architecture.priority_leak_audit_adjudication import read, summarize, write_summary
from trait_architecture.priority_leak_audit_overlay import (
    materialize_abstract_adjudication,
    read_overlay,
    write_sheet,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet_csv")
    parser.add_argument("overrides_csv")
    parser.add_argument("output_sheet_csv")
    parser.add_argument("output_dir")
    args = parser.parse_args(argv)

    packet = read(args.packet_csv)
    sheet = materialize_abstract_adjudication(packet, read_overlay(args.overrides_csv))
    write_sheet(args.output_sheet_csv, sheet)
    summary, comparisons, diagnostics = summarize(sheet)
    write_summary(args.output_dir, summary, comparisons, diagnostics)
    print(
        f"audit_rows={len(sheet)} screenable_rows={sum(row['route_screen_status'] != 'unassessed' for row in sheet)} "
        f"route_groups={len(summary)} route_comparisons={len(comparisons)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
