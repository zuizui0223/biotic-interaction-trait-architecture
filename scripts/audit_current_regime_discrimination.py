"""Audit whether existing directional evidence discriminates declared Part I scenarios.

Usage:
    python scripts/audit_current_regime_discrimination.py \
      configs/part_i_robustness_grid.json \
      artifacts/part_i/part_i_functional_form_summary.csv \
      artifacts/broad_meta/broad_direction_map.csv \
      artifacts/regime_discrimination
"""

from __future__ import annotations

import argparse
import json

from trait_architecture.regime_discrimination_audit import write_audit_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("part_i_config_json")
    parser.add_argument("functional_summary_csv")
    parser.add_argument("direction_map_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)

    report = write_audit_outputs(
        args.out_dir,
        config_path=args.part_i_config_json,
        functional_summary_path=args.functional_summary_csv,
        direction_map_path=args.direction_map_csv,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
