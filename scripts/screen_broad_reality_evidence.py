"""Create metadata-only shallow-screen outputs from the broad evidence corpus.

Usage:
    python scripts/screen_broad_reality_evidence.py \
      artifacts/broad_reality_evidence/broad_reality_evidence_candidates.csv \
      artifacts/broad_reality_evidence
"""

from __future__ import annotations

import argparse
import json

from trait_architecture.broad_reality_screen import (
    read_candidate_rows,
    screen_rows,
    screen_summary,
    write_screen_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)

    rows, fields = read_candidate_rows(args.candidate_csv)
    screened = screen_rows(rows)
    write_screen_outputs(args.out_dir, screened, fields)
    print(json.dumps(screen_summary(screened), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
