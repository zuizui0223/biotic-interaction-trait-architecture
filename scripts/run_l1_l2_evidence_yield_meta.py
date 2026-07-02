"""Run fixed-corpus L1/L2 evidence-yield meta-analysis.

Usage:
    python scripts/run_l1_l2_evidence_yield_meta.py \
      artifacts/broad_reality_evidence/broad_reality_evidence_screened.csv \
      empirical/broad_reality_evidence/priority_leak_audit/priority_leak_audit_yield_by_route_group_v1.csv \
      artifacts/l1_l2_evidence_yield_meta
"""

from __future__ import annotations

import argparse

from trait_architecture.evidence_yield_meta_analysis import AUDIT_FIELDS, SCREEN_FIELDS, read_rows
from trait_architecture.evidence_yield_meta_model import build_evidence_yield_meta, write_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("screened_csv")
    parser.add_argument("audit_yield_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)
    outputs = build_evidence_yield_meta(
        read_rows(args.screened_csv, SCREEN_FIELDS),
        read_rows(args.audit_yield_csv, AUDIT_FIELDS),
    )
    write_outputs(args.out_dir, *outputs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
