"""Classify matched floral-regime study cards.

Usage:
    python examples/audit_matched_flower_studies.py \
      empirical/matched_flower_regime/matched_flower_study_cards.csv

The output is a structural evidence classification, not a result about trait
selection or adaptation.
"""

from __future__ import annotations

import json
import sys

from trait_architecture.matched_regime_registry import (
    audit_matched_study_cards_file,
    matched_study_report_to_dict,
)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(
            "usage: python examples/audit_matched_flower_studies.py matched_flower_study_cards.csv"
        )
    report = audit_matched_study_cards_file(sys.argv[1])
    print(json.dumps(matched_study_report_to_dict(report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
