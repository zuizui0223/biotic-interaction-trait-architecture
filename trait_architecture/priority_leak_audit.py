"""Create route-stratified audit samples to test priority-screen leakage.

The sampler never redefines the inclusion rule. It creates matched reading queues
from already-screened candidates so direct-route source coding can compare
priority candidates with biologically contextual non-priority candidates.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

AUDIT_FIELDS = (
    "audit_group", "route_family_audit", "audit_rank", "candidate_id", "doi", "title",
    "publication_year", "container_title", "landing_page_url", "source_queries", "route_families",
    "metadata_A_signal", "metadata_B_signal", "metadata_P_signal", "metadata_H_signal", "metadata_W_signal",
    "metadata_biology_context_term_count", "shallow_screen_status", "shallow_screen_reason",
)

PRIORITY = "priority_for_shallow_source_coding"
BIOLOGICAL_NONPRIORITY = "biological_context_needs_route_screen"


def _stable_rank(seed: str, candidate_id: str, route: str, group: str) -> str:
    return hashlib.sha256(f"{seed}|{candidate_id}|{route}|{group}".encode("utf-8")).hexdigest()


def _routes(row: dict[str, str]) -> set[str]:
    return {route for route in row.get("route_families", "").split(";") if route}


def _eligible(row: dict[str, str], route: str, group: str) -> bool:
    return row.get("shallow_screen_status") == group and route in _routes(row)


def build_audit_sample(
    rows: Iterable[dict[str, str]], *, per_route_per_group: int = 30, seed: str = "priority-leak-audit-v1"
) -> tuple[list[dict[str, str]], dict[str, object]]:
    """Create matched priority vs biological-nonpriority reading queues per route."""
    if per_route_per_group < 1:
        raise ValueError("per_route_per_group must be positive")
    rows = list(rows)
    route_families = sorted({route for row in rows for route in _routes(row)})
    groups = (PRIORITY, BIOLOGICAL_NONPRIORITY)
    output: list[dict[str, str]] = []
    availability: dict[str, dict[str, int]] = {}
    for route in route_families:
        availability[route] = {}
        for group in groups:
            candidates = [row for row in rows if _eligible(row, route, group)]
            candidates.sort(key=lambda row: _stable_rank(seed, row.get("candidate_id", ""), route, group))
            selected = candidates[:per_route_per_group]
            availability[route][group] = len(candidates)
            for rank, row in enumerate(selected, start=1):
                output.append({
                    "audit_group": "priority" if group == PRIORITY else "biological_nonpriority",
                    "route_family_audit": route,
                    "audit_rank": str(rank),
                    **row,
                })
    summary = {
        "seed": seed,
        "per_route_per_group_requested": per_route_per_group,
        "route_families": route_families,
        "availability_by_route_and_group": availability,
        "sampled_row_count": len(output),
        "interpretation_boundary": (
            "This audit queue tests whether the metadata priority rule loses direct-route studies. "
            "It is not an included-study set and does not itself establish effects or directions."
        ),
    }
    return output, summary


def read_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_audit_outputs(input_csv: str | Path, out_dir: str | Path, *, per_route_per_group: int = 30) -> dict[str, object]:
    rows = read_rows(input_csv)
    sample, summary = build_audit_sample(rows, per_route_per_group=per_route_per_group)
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    with (destination / "priority_leak_audit_queue.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sample)
    (destination / "priority_leak_audit_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary
