"""Inspect CSV headers from a title-validated Dryad version archive."""

from __future__ import annotations

import argparse
import json

from trait_architecture.dryad_archive_schema import inspect_targets, write_schemas
from trait_architecture.title_validated_dryad_manifest import _fetch_json, read_targets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets_csv")
    parser.add_argument("out_dir")
    parser.add_argument("--endpoint-timeout-seconds", type=int, default=15)
    args = parser.parse_args(argv)
    if args.endpoint_timeout_seconds <= 0:
        raise ValueError("endpoint-timeout-seconds must be positive")

    def fetch_with_bound(url: str):
        return _fetch_json(url, timeout=args.endpoint_timeout_seconds)

    rows, report = inspect_targets(read_targets(args.targets_csv), fetch_json=fetch_with_bound)
    report["endpoint_timeout_seconds"] = args.endpoint_timeout_seconds
    write_schemas(args.out_dir, rows, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
