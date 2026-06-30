"""Validate DataCite-discovered dataset candidates before table inspection."""

from __future__ import annotations

import argparse
import json

from trait_architecture.public_dataset_link_validation import (
    _fetch_json,
    read_candidates,
    validate_candidates,
    write_receipts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates_csv")
    parser.add_argument("out_dir")
    parser.add_argument("--endpoint-timeout-seconds", type=int, default=10)
    args = parser.parse_args(argv)
    if args.endpoint_timeout_seconds <= 0:
        raise ValueError("endpoint-timeout-seconds must be positive")

    def fetch_with_bound(url: str):
        return _fetch_json(url, timeout=args.endpoint_timeout_seconds)

    rows = read_candidates(args.candidates_csv)
    receipts, report = validate_candidates(rows, fetch_json=fetch_with_bound)
    report["endpoint_timeout_seconds"] = args.endpoint_timeout_seconds
    write_receipts(args.out_dir, receipts, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
