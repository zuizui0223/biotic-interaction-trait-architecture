"""Build explicit layer gates and an exact-stratum meta-analysis intake queue.

Usage:
    python scripts/build_meta_analysis_intake.py \
      artifacts/broad_reality_evidence/broad_reality_evidence_candidates.csv \
      artifacts/broad_reality_evidence/broad_reality_evidence_screened.csv \
      empirical/broad_reality_evidence/priority_leak_audit/priority_leak_audit_yield_v1.csv \
      empirical/broad_reality_evidence/broad_route_records.csv \
      empirical/broad_reality_evidence/broad_meta_analysis_strata.csv \
      empirical/broad_reality_evidence/broad_effect_extractions.csv \
      empirical/broad_reality_evidence/precision_expansions/fulltext/B_TO_P_FULLTEXT_READING_QUEUE_v1.csv \
      artifacts/meta_analysis_intake
"""

from __future__ import annotations

import argparse
from pathlib import Path

from trait_architecture.meta_analysis_intake import (
    build_intake,
    read_rows,
    write_intake_outputs,
)
from trait_architecture.broad_meta_analysis import EFFECT_FIELDS, ROUTE_RECORD_FIELDS, STRATUM_FIELDS


CANDIDATE_FIELDS = ("candidate_id", "route_families")
SCREENED_FIELDS = ("candidate_id", "route_families", "shallow_screen_status")
AUDIT_FIELDS = (
    "route_family_audit", "audit_group", "sampled_rows", "route_screenable_rows",
    "direct_route_present_rows", "direct_route_absent_rows", "unassessed_rows",
)
FULLTEXT_FIELDS = (
    "queue_id", "study_cluster_id", "doi", "outcome_layer", "comparability_cell",
    "full_text_state", "analysis_action",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates_csv")
    parser.add_argument("screened_csv")
    parser.add_argument("audit_csv")
    parser.add_argument("route_records_csv")
    parser.add_argument("strata_csv")
    parser.add_argument("effects_csv")
    parser.add_argument("fulltext_queue_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)

    outputs = build_intake(
        read_rows(args.candidates_csv, CANDIDATE_FIELDS),
        read_rows(args.screened_csv, SCREENED_FIELDS),
        read_rows(args.audit_csv, AUDIT_FIELDS),
        read_rows(args.route_records_csv, ROUTE_RECORD_FIELDS),
        read_rows(args.strata_csv, STRATUM_FIELDS),
        read_rows(args.effects_csv, EFFECT_FIELDS),
        read_rows(args.fulltext_queue_csv, FULLTEXT_FIELDS),
    )
    write_intake_outputs(Path(args.out_dir), *outputs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
