"""Bulk scout public-source availability for OpenAlex matched-flower candidates.

This is deliberately shallow and broad. It reuses the OpenAlex seed harvest,
then records source availability for every DOI-bearing candidate without reading
article tables or extracting effects.

Usage:
    python scripts/bulk_scout_openalex_public_sources.py \
      empirical/matched_flower_regime/literature_seed_queries.csv \
      artifacts/bulk_public_source_scout \
      --results-per-query 50
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.harvest_openalex_matched_flower_seeds import (  # noqa: E402
    harvest,
    rank_key,
    read_query_registry,
    write_csv,
)
from trait_architecture.public_article_source_scout import audit_study_sources  # noqa: E402


SCOUT_STATUS_ORDER = {
    "public_fulltext_candidate": 100,
    "public_landing_candidate": 75,
    "content_link_discovered": 60,
    "linked_repository_manifest": 55,
    "linked_repository_candidate": 40,
    "metadata_recovered": 20,
    "not_found": 0,
    "access_failed": -5,
}


@dataclass(frozen=True)
class BulkScoutRow:
    candidate_id: str
    title: str
    doi: str
    publication_year: str
    seed_routes: str
    metadata_match_score: str
    metadata_attraction_signal: str
    metadata_barrier_signal: str
    metadata_pollination_signal: str
    metadata_antagonist_signal: str
    metadata_recoverability_signal: str
    openalex_is_open_access: str
    openalex_open_access_url: str
    receipt_count: int
    best_public_source_status: str
    public_pdf_candidate_count: int
    publisher_content_link_count: int
    public_landing_candidate_count: int
    linked_repository_manifest_count: int
    linked_repository_candidate_count: int
    access_failed_count: int
    source_availability_score: int
    broad_screen_priority: str
    next_action: str


BULK_FIELDS = tuple(BulkScoutRow.__dataclass_fields__)


def _text(value: object) -> str:
    return str(value or "").strip()


def _status_score(status: str) -> int:
    return SCOUT_STATUS_ORDER.get(status, 0)


def _best_status(statuses: Iterable[str]) -> str:
    labels = sorted(set(statuses), key=lambda item: (-_status_score(item), item))
    return labels[0] if labels else "no_receipts"


def _priority(row: BulkScoutRow) -> str:
    if row.public_pdf_candidate_count or row.linked_repository_manifest_count:
        if row.metadata_pollination_signal == "True" and row.metadata_antagonist_signal == "True":
            return "manual_screen_high"
        return "manual_screen_medium"
    if row.public_landing_candidate_count or row.publisher_content_link_count:
        return "source_route_followup"
    return "hold_metadata_only"


def _next_action(priority: str) -> str:
    if priority == "manual_screen_high":
        return "Screen public full text or verified manifest for trait/outcome denominators and reported effects."
    if priority == "manual_screen_medium":
        return "Check whether missing channel signal is absent or only missed by metadata before effect extraction."
    if priority == "source_route_followup":
        return "Verify access route and identity before any table or trait-function screen."
    return "Do not manually read until public source route improves or all higher-priority candidates are exhausted."


def build_row(candidate, receipts_report: dict[str, object]) -> BulkScoutRow:
    counts = receipts_report.get("counts_by_status") if isinstance(receipts_report, dict) else {}
    if not isinstance(counts, dict):
        counts = {}
    best = _best_status(str(key) for key in counts)
    source_score = max((_status_score(str(key)) for key, count in counts.items() if int(count or 0) > 0), default=0)
    if bool(candidate.is_open_access):
        source_score += 10
    if candidate.metadata_match_score:
        source_score += int(candidate.metadata_match_score)
    rough = BulkScoutRow(
        candidate_id=candidate.candidate_id,
        title=candidate.title,
        doi=candidate.doi,
        publication_year=str(candidate.publication_year),
        seed_routes=";".join(sorted(candidate.seed_routes)),
        metadata_match_score=str(candidate.metadata_match_score),
        metadata_attraction_signal=str(candidate.metadata_attraction_signal),
        metadata_barrier_signal=str(candidate.metadata_barrier_signal),
        metadata_pollination_signal=str(candidate.metadata_pollination_signal),
        metadata_antagonist_signal=str(candidate.metadata_antagonist_signal),
        metadata_recoverability_signal=str(candidate.metadata_recoverability_signal),
        openalex_is_open_access=str(candidate.is_open_access),
        openalex_open_access_url=candidate.open_access_url,
        receipt_count=int(receipts_report.get("receipt_count") or 0),
        best_public_source_status=best,
        public_pdf_candidate_count=int(counts.get("public_fulltext_candidate", 0)),
        publisher_content_link_count=int(counts.get("content_link_discovered", 0)),
        public_landing_candidate_count=int(counts.get("public_landing_candidate", 0)),
        linked_repository_manifest_count=int(counts.get("linked_repository_manifest", 0)),
        linked_repository_candidate_count=int(counts.get("linked_repository_candidate", 0)),
        access_failed_count=int(counts.get("access_failed", 0)),
        source_availability_score=source_score,
        broad_screen_priority="pending",
        next_action="pending",
    )
    priority = _priority(rough)
    return BulkScoutRow(**{**asdict(rough), "broad_screen_priority": priority, "next_action": _next_action(priority)})


def build_error_row(candidate, error: Exception) -> tuple[BulkScoutRow, dict[str, object]]:
    report = {
        "candidate_id": candidate.candidate_id,
        "title": candidate.title,
        "publication_year": candidate.publication_year,
        "study_doi": candidate.doi,
        "receipt_count": 1,
        "counts_by_status": {"access_failed": 1},
        "error": f"{type(error).__name__}: {error}",
    }
    return build_row(candidate, report), report


def write_rows(path: Path, rows: Iterable[BulkScoutRow]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BULK_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query_registry")
    parser.add_argument("out_dir")
    parser.add_argument("--results-per-query", type=int, default=50)
    parser.add_argument("--mailto", default="")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    queries = read_query_registry(args.query_registry)
    candidates, query_reports = harvest(queries, args.results_per_query, args.mailto or None)
    all_candidates = sorted(candidates, key=rank_key)
    doi_candidates = [candidate for candidate in all_candidates if _text(candidate.doi)]

    write_csv(out_dir / "openalex_matched_flower_all_candidates.csv", all_candidates)

    scout_rows: list[BulkScoutRow] = []
    reports: list[dict[str, object]] = []
    for index, candidate in enumerate(doi_candidates, start=1):
        try:
            _receipts, report = audit_study_sources(
                study_doi=candidate.doi,
                queue_id=f"bulk_{index:04d}",
                study_id=candidate.candidate_id.replace(":", "_"),
            )
            report = {
                **report,
                "candidate_id": candidate.candidate_id,
                "title": candidate.title,
                "publication_year": candidate.publication_year,
                "metadata_match_score": candidate.metadata_match_score,
            }
            scout_rows.append(build_row(candidate, report))
            reports.append(report)
        except Exception as error:
            row, report = build_error_row(candidate, error)
            scout_rows.append(row)
            reports.append(report)

    scout_rows = sorted(
        scout_rows,
        key=lambda row: (-row.source_availability_score, row.broad_screen_priority, row.title.lower()),
    )
    write_rows(out_dir / "bulk_public_source_scout_ranked.csv", scout_rows)
    (out_dir / "bulk_public_source_scout_reports.json").write_text(
        json.dumps(reports, indent=2, sort_keys=True), encoding="utf-8"
    )
    summary = {
        "source": "OpenAlex + Crossref/OpenAlex/DataCite/Dryad/Zenodo source scout",
        "purpose": "shallow broad public-source triage only; no table reading, effect extraction, or evidence promotion",
        "query_registry": args.query_registry,
        "results_per_query": args.results_per_query,
        "query_reports": query_reports,
        "unique_candidates": len(all_candidates),
        "doi_candidates_screened": len(doi_candidates),
        "manual_screen_high": sum(row.broad_screen_priority == "manual_screen_high" for row in scout_rows),
        "manual_screen_medium": sum(row.broad_screen_priority == "manual_screen_medium" for row in scout_rows),
        "source_route_followup": sum(row.broad_screen_priority == "source_route_followup" for row in scout_rows),
        "hold_metadata_only": sum(row.broad_screen_priority == "hold_metadata_only" for row in scout_rows),
        "access_failed_rows": sum(row.access_failed_count > 0 for row in scout_rows),
        "status": "success" if scout_rows else "no_doi_candidates",
        "warning": "A public source route is not an effect. Manual screening must still verify trait function, denominators, site-time alignment, and uncertainty.",
    }
    (out_dir / "bulk_public_source_scout_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
