"""Audit four-path floral interaction effect records.

Usage:
    python examples/audit_four_path_effects.py \
      empirical/four_path_effects/four_path_effect_registry.csv
"""

from __future__ import annotations

import argparse
import json

from trait_architecture.four_path_effects import (
    audit_effect_registry_file,
    effect_registry_report_to_dict,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry_csv")
    args = parser.parse_args()
    report = audit_effect_registry_file(args.registry_csv)
    print(json.dumps(effect_registry_report_to_dict(report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
