"""Build a matched priority vs biological-nonpriority audit queue.

Usage:
  python scripts/build_priority_leak_audit.py INPUT_SCREENED.csv OUT_DIR --per-route-per-group 30
"""
from __future__ import annotations
import argparse, json
from trait_architecture.priority_leak_audit import write_audit_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_screened_csv")
    parser.add_argument("out_dir")
    parser.add_argument("--per-route-per-group", type=int, default=30)
    args = parser.parse_args(argv)
    summary = write_audit_outputs(
        args.input_screened_csv, args.out_dir, per_route_per_group=args.per_route_per_group
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
