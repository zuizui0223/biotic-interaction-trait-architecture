"""Validate the current Part I robustness and broad-meta-analysis boundary.

Usage:
    python scripts/validate_current_theory_meta.py \
      configs/part_i_robustness_grid.json \
      artifacts/part_i/part_i_robustness_report.json \
      artifacts/broad_meta/broad_direction_map.csv \
      artifacts/broad_meta/broad_meta_analysis_summary.csv \
      artifacts/theory_meta_validation
"""

from __future__ import annotations

import argparse
import json

from trait_architecture.theory_meta_validation import write_validation_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("part_i_config_json")
    parser.add_argument("part_i_report_json")
    parser.add_argument("direction_map_csv")
    parser.add_argument("quantitative_summary_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)

    report = write_validation_outputs(
        args.out_dir,
        part_i_config_path=args.part_i_config_json,
        part_i_report_path=args.part_i_report_json,
        direction_map_path=args.direction_map_csv,
        quantitative_summary_path=args.quantitative_summary_csv,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
