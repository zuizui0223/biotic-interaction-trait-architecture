"""Rank harvested OpenAlex candidates by shallow public-source availability.

Usage:
    python scripts/rank_broad_public_source_availability.py \
      artifacts/matched_flower_seed_harvest/openalex_matched_flower_all_candidates.csv \
      artifacts/broad_public_source_availability \
      --exclude-screened-queue empirical/four_path_effects/four_path_screen_queue.csv
"""

from __future__ import annotations

import argparse
import json

from trait_architecture.broad_source_availability import (
    filter_unscreened,
    rank_candidates,
    read_already_screened_dois,
    read_harvest,
    write_outputs,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("harvest_csv")
    parser.add_argument("out_dir")
    parser.add_argument("--top-n", type=int, default=40)
    parser.add_argument("--exclude-screened-queue", default="")
    args = parser.parse_args(argv)
    rows = read_harvest(args.harvest_csv)
    excluded = read_already_screened_dois(args.exclude_screened_queue) if args.exclude_screened_queue else set()
    filtered = filter_unscreened(rows, excluded)
    records = rank_candidates(filtered)
    summary = write_outputs(
        records,
        args.out_dir,
        top_n=args.top_n,
        original_candidate_count=len(rows),
        excluded_screened_count=len(rows) - len(filtered),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
