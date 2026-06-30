"""Batch-scout public source routes across harvested matched-flower candidates.

The input is the complete OpenAlex candidate universe from the matched-flower
harvest. This module is deliberately shallow and broad: it records DOI-exact
public-source routes and ranks retrieval leads, but it does not read article
tables, download datasets, classify traits, or create effect records.
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from trait_architecture.public_article_source_scout import (
    ArticleSourceReceipt,
    audit_study_sources,
    normalise_doi,
)


INPUT_REQUIRED = {
    "candidate_id", "seed_routes", "seed_query_ids", "title", "doi",
    "authors", "publication_year", "publication_date", "work_type",
    "landing_page_url", "open_access_url", "is_open_access", "metadata_match_score",
    "metadata_attraction_signal", "metadata_barrier_signal", "metadata_pollination_signal",
    "metadata_antagonist_signal", "metadata_recoverability_signal", "candidate_status",
}

SUMMARY_FIELDS = [
    "candidate_id", "title", "doi", "publication_year", "authors", "seed_routes",
    "metadata_match_score", "metadata_attraction_signal", "metadata_barrier_signal",
    "metadata_pollination_signal", "metadata_antagonist_signal", "metadata_recoverability_signal",
    "receipt_count", "metadata_recovered_count", "publisher_content_link_count",
    "public_fulltext_candidate_count", "public_landing_candidate_count",
    "linked_repository_manifest_count", "linked_repository_candidate_count",
    "repository_access_failed_count", "repository_not_found_count", "source_priority_score",
    "public_source_action", "automatic_evidence_level", "automatic_screen_warning",
]

RECEIPT_FIELDS = [
    "candidate_id", "title", "doi", "provider", "source_kind", "resolution_status",
    "request_url", "source_identifier", "landing_page_url", "content_url", "content_type",
    "license_label", "relation_to_article", "notes",
]

POSITIVE_STATUSES = {
    "publisher_content_link": 2,
    "public_fulltext_candidate": 8,
    "public_landing_candidate": 3,
    "linked_repository_manifest": 12,
    "linked_repository_candidate": 6,
}


def text(value: object) -> str:
    return str(value or "").strip()


def truthy(value: object) -> bool:
    return text(value).lower() in {"1", "true", "yes", "y"}


def read_candidates(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = [{key: text(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    if not rows:
        raise ValueError("candidate CSV is empty")
    missing = sorted(INPUT_REQUIRED.difference(rows[0]))
    if missing:
        raise ValueError(f"candidate CSV missing required columns: {', '.join(missing)}")
    return rows


def _status_count(receipts: Iterable[ArticleSourceReceipt], status: str) -> int:
    return sum(receipt.resolution_status == status for receipt in receipts)


def _kind_count(receipts: Iterable[ArticleSourceReceipt], kind: str) -> int:
    return sum(receipt.source_kind == kind for receipt in receipts)


def _metadata_score(row: dict[str, str]) -> int:
    base = int(row.get("metadata_match_score") or 0) * 10
    base += 4 if truthy(row.get("metadata_attraction_signal")) else 0
    base += 4 if truthy(row.get("metadata_barrier_signal")) else 0
    base += 4 if truthy(row.get("metadata_pollination_signal")) else 0
    base += 4 if truthy(row.get("metadata_antagonist_signal")) else 0
    base += 2 if truthy(row.get("metadata_recoverability_signal")) else 0
    return base


def priority_score(row: dict[str, str], receipts: list[ArticleSourceReceipt]) -> int:
    score = _metadata_score(row)
    score += 4 if truthy(row.get("is_open_access")) else 0
    score += 4 if text(row.get("open_access_url")) else 0
    for receipt in receipts:
        score += POSITIVE_STATUSES.get(receipt.resolution_status, 0)
    return score


def action_for(receipts: list[ArticleSourceReceipt]) -> str:
    if any(receipt.resolution_status == "linked_repository_manifest" for receipt in receipts):
        return "inspect_repository_manifest_then_screen_tables"
    if any(receipt.resolution_status == "public_fulltext_candidate" for receipt in receipts):
        return "inspect_public_full_text_for_methods_tables_and_supplements"
    if any(receipt.resolution_status == "linked_repository_candidate" for receipt in receipts):
        return "verify_repository_identity_before_table_screen"
    if any(receipt.resolution_status in {"publisher_content_link", "public_landing_candidate"} for receipt in receipts):
        return "inspect_landing_or_publisher_links_for_accessible_supplements"
    return "retain_m0_no_public_route_discovered"


def summarize(row: dict[str, str], receipts: list[ArticleSourceReceipt]) -> dict[str, object]:
    return {
        "candidate_id": row["candidate_id"],
        "title": row["title"],
        "doi": normalise_doi(row["doi"]),
        "publication_year": row.get("publication_year", ""),
        "authors": row.get("authors", ""),
        "seed_routes": row.get("seed_routes", ""),
        "metadata_match_score": row.get("metadata_match_score", ""),
        "metadata_attraction_signal": row.get("metadata_attraction_signal", ""),
        "metadata_barrier_signal": row.get("metadata_barrier_signal", ""),
        "metadata_pollination_signal": row.get("metadata_pollination_signal", ""),
        "metadata_antagonist_signal": row.get("metadata_antagonist_signal", ""),
        "metadata_recoverability_signal": row.get("metadata_recoverability_signal", ""),
        "receipt_count": len(receipts),
        "metadata_recovered_count": _status_count(receipts, "metadata_recovered"),
        "publisher_content_link_count": _kind_count(receipts, "publisher_content_link"),
        "public_fulltext_candidate_count": _status_count(receipts, "public_fulltext_candidate"),
        "public_landing_candidate_count": _status_count(receipts, "public_landing_candidate"),
        "linked_repository_manifest_count": _status_count(receipts, "linked_repository_manifest"),
        "linked_repository_candidate_count": _status_count(receipts, "linked_repository_candidate"),
        "repository_access_failed_count": _status_count(receipts, "access_failed"),
        "repository_not_found_count": _status_count(receipts, "not_found"),
        "source_priority_score": priority_score(row, receipts),
        "public_source_action": action_for(receipts),
        "automatic_evidence_level": "M0_public_source_lead_only",
        "automatic_screen_warning": (
            "Automatic source routes are retrieval leads only. Do not infer trait functions, denominators, "
            "effect signs, M1/M2/D1 status, or author-contact needs from this row."
        ),
    }


def receipt_rows(candidate: dict[str, str], receipts: list[ArticleSourceReceipt]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for receipt in receipts:
        payload = asdict(receipt)
        receipt_title = str(payload.pop("title", "") or "")
        rows.append({
            "candidate_id": candidate["candidate_id"],
            "title": candidate["title"] or receipt_title,
            "doi": normalise_doi(candidate["doi"]),
            **{key: payload[key] for key in payload if key in RECEIPT_FIELDS},
        })
    return rows


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run(input_csv: str | Path, out_dir: str | Path, *, limit: int, sleep_seconds: float) -> dict[str, object]:
    candidates = [row for row in read_candidates(input_csv) if normalise_doi(row.get("doi"))]
    if limit > 0:
        candidates = candidates[:limit]
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)

    summaries: list[dict[str, object]] = []
    receipts_flat: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for index, candidate in enumerate(candidates, start=1):
        doi = normalise_doi(candidate["doi"])
        try:
            receipts, _ = audit_study_sources(
                study_doi=doi,
                queue_id=candidate["candidate_id"],
                study_id=candidate["candidate_id"],
            )
            summaries.append(summarize(candidate, receipts))
            receipts_flat.extend(receipt_rows(candidate, receipts))
        except Exception as error:
            failures.append({
                "candidate_id": candidate["candidate_id"],
                "doi": doi,
                "title": candidate["title"],
                "error_type": type(error).__name__,
                "message": str(error),
            })
        if sleep_seconds and index < len(candidates):
            time.sleep(sleep_seconds)

    summaries_sorted = sorted(
        summaries,
        key=lambda row: (-int(row["source_priority_score"]), str(row["title"]).lower()),
    )
    positives = [row for row in summaries_sorted if row["public_source_action"] != "retain_m0_no_public_route_discovered"]
    write_csv(output / "batch_public_source_summary.csv", SUMMARY_FIELDS, summaries_sorted)
    write_csv(output / "batch_public_source_positive_leads.csv", SUMMARY_FIELDS, positives)
    write_csv(output / "batch_public_source_receipts.csv", RECEIPT_FIELDS, receipts_flat)
    write_csv(output / "batch_public_source_failures.csv", ["candidate_id", "doi", "title", "error_type", "message"], failures)

    counts_by_action: dict[str, int] = {}
    for row in summaries_sorted:
        action = str(row["public_source_action"])
        counts_by_action[action] = counts_by_action.get(action, 0) + 1
    report = {
        "input_csv": str(input_csv),
        "candidate_rows_with_doi": len(candidates),
        "screened_count": len(summaries_sorted),
        "positive_lead_count": len(positives),
        "failure_count": len(failures),
        "counts_by_action": counts_by_action,
        "top_positive_leads_preview": [
            {
                "candidate_id": row["candidate_id"],
                "title": row["title"],
                "doi": row["doi"],
                "score": row["source_priority_score"],
                "action": row["public_source_action"],
            }
            for row in positives[:20]
        ],
        "decision_boundary": (
            "This is a broad public-route screen. It does not inspect full text, traits, denominators, "
            "or effects; every row remains M0 until manual source screening."
        ),
    }
    (output / "batch_public_source_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    return report
