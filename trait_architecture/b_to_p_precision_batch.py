"""Select B-to-pollination precision candidates with both B and P metadata signals.

This is an access-first source-screening queue, not a biological role assignment.
The metadata signals merely target likely candidates; direct B role still requires
source review under the B-to-P precision protocol.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


QUEUE_FIELDS = (
    "queue_rank", "candidate_id", "doi", "title", "focus_route_families",
    "all_discovery_route_families", "abstract_available", "metadata_review_signal",
    "metadata_B_signal", "metadata_P_signal", "query_rank_min",
    "calibration_selection_rule", "coding_status",
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


def select_b_to_p_precision_batch(
    priority_candidates: Iterable[dict[str, str]], *, limit: int = 25
) -> list[dict[str, str]]:
    """Return B/P signal-positive candidates in a deterministic access-first order."""

    if limit < 1:
        raise ValueError("limit must be >= 1")
    selected = [
        dict(row) for row in priority_candidates
        if _bool(row.get("metadata_B_signal")) and _bool(row.get("metadata_P_signal"))
    ]
    seen: set[str] = set()
    rows: list[dict[str, str]] = []
    for candidate in sorted(
        selected,
        key=lambda row: (
            0 if _bool(row.get("abstract_available")) else 1,
            0 if not _bool(row.get("metadata_review_signal")) else 1,
            _rank(row.get("query_rank_min")),
            _text(row.get("candidate_id")),
        ),
    ):
        candidate_id = _text(candidate.get("candidate_id"))
        if not candidate_id or candidate_id in seen:
            continue
        seen.add(candidate_id)
        rows.append({
            "queue_rank": str(len(rows) + 1),
            "candidate_id": candidate_id,
            "doi": _text(candidate.get("doi")),
            "title": _text(candidate.get("title")),
            "focus_route_families": "B_to_pollination",
            "all_discovery_route_families": _text(candidate.get("route_families")),
            "abstract_available": str(_bool(candidate.get("abstract_available"))).lower(),
            "metadata_review_signal": str(_bool(candidate.get("metadata_review_signal"))).lower(),
            "metadata_B_signal": "true",
            "metadata_P_signal": "true",
            "query_rank_min": _text(candidate.get("query_rank_min")),
            "calibration_selection_rule": "B_and_P_metadata_signal_access_first_nonreview_first_query_rank",
            "coding_status": "unassessed",
        })
        if len(rows) >= limit:
            break
    return rows


def write_b_to_p_precision_batch(path: str | Path, rows: Iterable[dict[str, str]]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
