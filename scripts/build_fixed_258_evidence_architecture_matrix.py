"""Create the fixed all-258 evidence-architecture coding matrix.

The output contains archived retrieval metadata plus blank evidence-coding fields.
It is intentionally not an effect registry and contains no inferred biological
measurements.

Usage:
    python scripts/build_fixed_258_evidence_architecture_matrix.py artifacts/all_258
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from trait_architecture.evidence_architecture_audit import (
    initial_screening_rows,
    metadata_baseline_summary,
    write_matrix,
    write_metadata_baseline,
)
from trait_architecture.fixed_candidate_universe import load_fixed_candidate_universe


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)

    candidates, receipt = load_fixed_candidate_universe()
    rows = initial_screening_rows(candidates)
    out_dir = Path(args.out_dir)
    write_matrix(out_dir / "fixed_258_screening_matrix.csv", rows)
    write_metadata_baseline(out_dir / "fixed_258_metadata_baseline.json", rows)
    (out_dir / "fixed_258_snapshot_receipt.json").write_text(
        json.dumps({
            "source_pr": receipt.source_pr,
            "source_workflow_run": receipt.source_workflow_run,
            "source_artifact_id": receipt.source_artifact_id,
            "source_member": receipt.source_member,
            "artifact_sha256": receipt.artifact_sha256,
            "candidate_count": receipt.candidate_count,
        }, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(metadata_baseline_summary(rows), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
