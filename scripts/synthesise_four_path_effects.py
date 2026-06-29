"""Synthesize effect-size strata from the four-path floral registry.

This CLI reports separate DerSimonian–Laird random-effects summaries by
`effect_role × effect_measure × causal_status`. It does not transform across
scales or assign the resulting values directly to model parameters.

Usage:
    python scripts/synthesise_four_path_effects.py \
      empirical/four_path_effects/four_path_effect_registry.csv \
      artifacts/four_path_synthesis
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path

from trait_architecture.effect_synthesis import (
    synthesise_effect_registry,
    synthesis_report_to_dict,
)
from trait_architecture.four_path_effects import read_effect_registry


SUMMARY_FIELDS = [
    "effect_role",
    "effect_measure",
    "causal_status",
    "parameter_target",
    "n_effects",
    "n_studies",
    "fixed_effect_estimate",
    "random_effect_estimate",
    "random_effect_se",
    "ci95_lower",
    "ci95_upper",
    "tau2",
    "q",
    "q_df",
    "i2_percent",
    "synthesis_status",
    "notes",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)

    summaries, warnings = synthesise_effect_registry(read_effect_registry(args.registry_csv))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "four_path_scale_specific_summaries.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for summary in summaries:
            writer.writerow(asdict(summary))
    report = synthesis_report_to_dict(summaries, warnings)
    (out_dir / "four_path_synthesis_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
