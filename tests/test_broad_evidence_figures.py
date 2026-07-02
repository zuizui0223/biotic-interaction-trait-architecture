"""Smoke test: the primary-product figures regenerate from committed inputs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
BROAD = ROOT / "empirical" / "broad_reality_evidence"


def test_primary_figures_render_valid_svg(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "scripts/plot_broad_evidence_primary_figures.py",
            str(BROAD / "broad_route_records.csv"),
            str(BROAD / "priority_leak_audit" / "priority_leak_audit_yield_by_route_group_v1.csv"),
            str(tmp_path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"figure script failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"

    for name in ("fig1_direction_map.svg", "fig2_yield_meta_analysis.svg"):
        svg = (tmp_path / name).read_text(encoding="utf-8")
        assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
        assert "<rect" in svg and "<text" in svg
    # the one supported cell and the pooled enrichment estimate must be drawn
    assert "mostly compatible" in (tmp_path / "fig1_direction_map.svg").read_text(encoding="utf-8")
    assert "pooled 1.47" in (tmp_path / "fig2_yield_meta_analysis.svg").read_text(encoding="utf-8")
