"""Run the active theory-to-effect research pipeline in the declared order.

The pipeline is intentionally staged:

1. qualitative Part I functional-form and parameter-envelope robustness;
2. four-path effect-registry audit;
3. scale-specific effect synthesis;
4. explicit parameter-envelope bridge readiness; and
5. direct matched-study (D1–D3) case audit.

It does not silently turn empty evidence tables into calibrated parameters. An
empty effect registry yields a valid synthesis/bridge report that says the
empirical envelope is not ready.

Usage:
    python scripts/run_research_pipeline.py artifacts/research_pipeline
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from trait_architecture.matched_regime_registry import (
    audit_matched_study_cards_file,
    matched_study_report_to_dict,
)


ROOT = Path(__file__).parents[1]


def _run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    robustness_dir = out_dir / "01_part_i_robustness"
    synthesis_dir = out_dir / "03_four_path_synthesis"
    bridge_dir = out_dir / "04_parameter_envelope_bridge"
    direct_case_dir = out_dir / "05_direct_case_audit"

    _run(
        [
            sys.executable,
            "scripts/run_part_i_robustness.py",
            "configs/part_i_robustness_grid.json",
            str(robustness_dir),
        ]
    )
    _run(
        [
            sys.executable,
            "scripts/synthesise_four_path_effects.py",
            "empirical/four_path_effects/four_path_effect_registry.csv",
            str(synthesis_dir),
        ]
    )
    _run(
        [
            sys.executable,
            "scripts/validate_parameter_envelope_bridge.py",
            "configs/four_path_parameter_envelope_contracts.json",
            str(synthesis_dir / "four_path_scale_specific_summaries.csv"),
            str(bridge_dir),
        ]
    )

    direct_case_dir.mkdir(parents=True, exist_ok=True)
    direct_case_report = audit_matched_study_cards_file(
        ROOT / "empirical/matched_flower_regime/matched_flower_study_cards.csv"
    )
    (direct_case_dir / "matched_study_audit.json").write_text(
        json.dumps(matched_study_report_to_dict(direct_case_report), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    bridge_report = json.loads(
        (bridge_dir / "parameter_envelope_readiness.json").read_text(encoding="utf-8")
    )
    manifest = {
        "pipeline_order": [
            "01_part_i_robustness",
            "02_four_path_registry_audit_via_synthesis",
            "03_four_path_synthesis",
            "04_parameter_envelope_bridge",
            "05_direct_case_audit",
        ],
        "outputs": {
            "robustness": str(robustness_dir.relative_to(ROOT)),
            "synthesis": str(synthesis_dir.relative_to(ROOT)),
            "parameter_bridge": str(bridge_dir.relative_to(ROOT)),
            "direct_case_audit": str(direct_case_dir.relative_to(ROOT)),
        },
        "all_empirical_channel_envelopes_ready": bridge_report["all_channels_ready"],
        "interpretation": "The pipeline is complete when robustness outputs, effect summaries, bridge readiness, and direct-case audit are all present. Parameter calibration remains blocked until explicit contracts are complete.",
    }
    (out_dir / "pipeline_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
