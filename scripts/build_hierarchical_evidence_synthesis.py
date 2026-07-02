"""Materialize the layered broad-evidence report from workflow artifacts.

Usage:
    python scripts/build_hierarchical_evidence_synthesis.py \
      artifacts/broad_reality_evidence/broad_reality_evidence_candidates.csv \
      artifacts/broad_reality_evidence/broad_reality_evidence_screened.csv \
      artifacts/broad_reality_evidence/priority_leak_audit/priority_leak_audit_yield_by_route_group.csv \
      empirical/broad_reality_evidence/broad_route_records.csv \
      empirical/broad_reality_evidence/broad_effect_extractions.csv \
      empirical/broad_reality_evidence/precision_expansions/fulltext/B_TO_P_FULLTEXT_READING_QUEUE_v1.csv \
      artifacts/hierarchical_evidence_synthesis
"""

from __future__ import annotations

import argparse
from pathlib import Path

from trait_architecture.hierarchical_evidence_synthesis import (
    AUDIT_REQUIRED,
    CANDIDATE_REQUIRED,
    EFFECT_REQUIRED,
    FULLTEXT_REQUIRED,
    ROUTE_RECORD_REQUIRED,
    SCREENED_REQUIRED,
    build_hierarchical_summary,
    read_rows,
    write_hierarchical_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates_csv")
    parser.add_argument("screened_csv")
    parser.add_argument("audit_summary_csv")
    parser.add_argument("route_records_csv")
    parser.add_argument("effect_extractions_csv")
    parser.add_argument("b_to_p_fulltext_queue_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)

    layer_rows, direction_rows, summary = build_hierarchical_summary(
        read_rows(args.candidates_csv, CANDIDATE_REQUIRED),
        read_rows(args.screened_csv, SCREENED_REQUIRED),
        read_rows(args.audit_summary_csv, AUDIT_REQUIRED),
        read_rows(args.route_records_csv, ROUTE_RECORD_REQUIRED),
        read_rows(args.effect_extractions_csv, EFFECT_REQUIRED),
        read_rows(args.b_to_p_fulltext_queue_csv, FULLTEXT_REQUIRED),
    )
    write_hierarchical_outputs(Path(args.out_dir), layer_rows, direction_rows, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
