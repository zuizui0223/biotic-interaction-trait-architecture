import json
import subprocess
import sys
from pathlib import Path


def test_research_pipeline_runs_without_pretending_empty_evidence_is_calibrated(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    out_dir = tmp_path / "pipeline"

    result = subprocess.run(
        [sys.executable, "scripts/run_research_pipeline.py", str(out_dir)],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "research pipeline failed\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    manifest = json.loads((out_dir / "pipeline_manifest.json").read_text(encoding="utf-8"))
    robustness = out_dir / "01_part_i_robustness"
    synthesis = out_dir / "03_four_path_synthesis"
    bridge = out_dir / "04_parameter_envelope_bridge"
    direct_cases = out_dir / "05_direct_case_audit"

    assert (robustness / "part_i_robustness_cases.csv").exists()
    assert (robustness / "part_i_functional_form_summary.csv").exists()
    assert (robustness / "part_i_robustness_envelope.csv").exists()
    assert (synthesis / "four_path_scale_specific_summaries.csv").exists()
    assert (bridge / "parameter_envelope_readiness.json").exists()
    assert (direct_cases / "matched_study_audit.json").exists()
    assert manifest["all_empirical_channel_envelopes_ready"] is False
