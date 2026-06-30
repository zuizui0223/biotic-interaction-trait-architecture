"""Batch-scout public source routes across harvested matched-flower candidates.

Usage:
    python scripts/batch_scout_public_sources.py \
      artifacts/matched_flower_seed_harvest/openalex_matched_flower_all_candidates.csv \
      artifacts/matched_flower_batch_public_sources \
      --limit 0
"""

from __future__ import annotations

import argparse
import json

from trait_architecture.batch_public_source_scout import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv")
    parser.add_argument("out_dir")
    parser.add_argument("--limit", type=int, default=0, help="0 means all rows with DOI")
    parser.add_argument("--sleep-seconds", type=float, default=0.05)
    args = parser.parse_args(argv)
    report = run(args.input_csv, args.out_dir, limit=args.limit, sleep_seconds=args.sleep_seconds)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
