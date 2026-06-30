"""Audit Gymnadenia table linkage without retaining raw observation rows.

Usage:
    python scripts/audit_gymnadenia_row_linkage.py \
      10.5061/dryad.dj40r \
      artifacts/gymnadenia_row_linkage
"""

from __future__ import annotations

import argparse
import json

from trait_architecture.gymnadenia_row_linkage import (
    audit_gymnadenia_row_linkage,
    write_gymnadenia_row_linkage_audit,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_doi")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)
    report = audit_gymnadenia_row_linkage(dataset_doi=args.dataset_doi)
    write_gymnadenia_row_linkage_audit(args.out_dir, report)
    print(json.dumps({
        "dataset_doi": report["dataset_doi"],
        "herbivory_denominator_contract": report["herbivory_denominator_contract"],
        "decision_boundary": report["decision_boundary"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
