"""Write receipts for article-declared Figshare accessions."""

from __future__ import annotations

import argparse
import json

from trait_architecture.declared_figshare_receipts import resolve_declared_figshare_queue
from trait_architecture.public_repository_resolver import read_queue, write_receipts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("queue_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)
    rows = read_queue(args.queue_csv)
    receipts, report = resolve_declared_figshare_queue(rows)
    write_receipts(args.out_dir, receipts, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
