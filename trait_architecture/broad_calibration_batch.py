"""Select a reproducible, route-balanced calibration batch from priority candidates.

Selection order is a workflow convenience only. It does not imply evidential
quality or biological direction.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Iterable


ROUTE_FAMILIES = (
    "A_to_pollination",
    "A_to_antagonism",
    "B_to_antagonism",
    "B_to_pollination",
    "joint_channels",
)
QUEUE_FIELDS = (
    "queue_rank", "candidate_id", "doi", "title", "focus_route_families",
    "all_discovery_route_families", "abstract_available", "metadata_review_signal",
    "query_rank_min", "calibration_selection_rule", "coding_status",
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _bool(value: object) -> bool:
    return _text(value).lower() in {"true", "1", "yes"}


def _rank(value: object) -> int:
    try:
        return int(_text(value))
    except ValueError:
        return 10**9


def _sort_key(row: dict[str, str]) -> tuple[int, int, int, str]:
    """Prefer source access cues, never scientific direction or citation count."""

    return (
        0 if _bool(row.get("abstract_available")) else 1,
        0 if not _bool(row.get("metadata_review_signal")) else 1,
        _rank(row.get("query_rank_min")),
        _text(row.get("candidate_id")),
    )


def select_calibration_batch(
    priority_candidates: Iterable[dict[str, str]], *, per_route: int = 10
) -> list[dict[str, str]]:
    """Return up to `per_route` candidates per discovery route, deduplicated globally."""

    if per_route < 1:
        raise ValueError("per_route must be >= 1")
    candidates = [dict(row) for row in priority_candidates]
    by_route: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        routes = {_text(route) for route in _text(row.get("route_families")).split(";") if _text(route)}
        for route in routes.intersection(ROUTE_FAMILIES):
            by_route[route].append(row)
    selected: dict[str, dict[str, object]] = {}
    for route in ROUTE_FAMILIES:
        for row in sorted(by_route[route], key=_sort_key)[:per_route]:
            candidate_id = _text(row.get("candidate_id"))
            if not candidate_id:
                raise ValueError("priority candidate has blank candidate_id")
            if candidate_id not in selected:
                selected[candidate_id] = {"row": row, "focus_routes": set()}
            selected[candidate_id]["focus_routes"].add(route)
    output: list[dict[str, str]] = []
    for rank, payload in enumerate(sorted(selected.values(), key=lambda item: _sort_key(item["row"])), start=1):
        row = payload["row"]
        output.append({
            "queue_rank": str(rank),
            "candidate_id": _text(row.get("candidate_id")),
            "doi": _text(row.get("doi")),
            "title": _text(row.get("title")),
            "focus_route_families": ";".join(sorted(payload["focus_routes"])),
            "all_discovery_route_families": _text(row.get("route_families")),
            "abstract_available": str(_bool(row.get("abstract_available"))).lower(),
            "metadata_review_signal": str(_bool(row.get("metadata_review_signal"))).lower(),
            "query_rank_min": _text(row.get("query_rank_min")),
            "calibration_selection_rule": "route_balanced_access_first_nonreview_first_query_rank",
            "coding_status": "unassessed",
        })
    return output


def write_calibration_batch(path: str | Path, rows: Iterable[dict[str, str]]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
