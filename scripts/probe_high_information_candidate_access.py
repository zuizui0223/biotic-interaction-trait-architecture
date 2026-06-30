"""Probe shallow public content access after the fixed 258-candidate audit.

Input is the metadata-only audit created in the same workflow. This command reads
no articles or tables: it obtains only a small byte prefix from predeclared
candidate URLs and checks exact repository-record relations for manifest-bearing
candidates.

Usage:
    python scripts/probe_high_information_candidate_access.py artifacts/fixed_258_public_routes
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from trait_architecture.high_information_access_probe import (
    _read_csv,
    run_access_probe,
    write_access_probe,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit_dir")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args(argv)
    audit_dir = Path(args.audit_dir)
    summaries, access, identities, report = run_access_probe(
        _read_csv(audit_dir / "fixed_258_candidate_source_audit.csv"),
        _read_csv(audit_dir / "fixed_258_candidate_source_receipts.csv"),
        max_workers=args.workers,
    )
    write_access_probe(audit_dir, summaries, access, identities, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
