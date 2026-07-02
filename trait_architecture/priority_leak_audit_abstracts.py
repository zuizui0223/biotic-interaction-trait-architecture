"""Retrieve Crossref abstract packets for the priority-leak audit queue.

The output preserves every audit stratum and rank so source coding can compare
priority and biological-nonpriority candidates using the same direct-route
codebook.  Metadata abstracts are screening aids only: they do not establish
trait measurement, effect direction, causal design, or quantitative eligibility.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Callable, Iterable

from trait_architecture.broad_calibration_abstracts import (
    CROSSREF_WORKS_URL,
    _plain_text,
    _request_json,
    _text,
    _year,
)
from urllib.parse import quote


PACKET_FIELDS = (
    "audit_group", "route_family_audit", "audit_rank", "candidate_id", "doi", "title",
    "publication_year", "container_title", "landing_page_url", "source_queries", "route_families",
    "metadata_A_signal", "metadata_B_signal", "metadata_P_signal", "metadata_H_signal", "metadata_W_signal",
    "metadata_biology_context_term_count", "shallow_screen_status", "shallow_screen_reason",
    "crossref_lookup_status", "crossref_message_type", "crossref_title", "crossref_published_year",
    "crossref_container_title", "crossref_abstract_available", "crossref_abstract_text", "source_packet_warning",
)

WARNING = (
    "Crossref metadata abstracts support source screening only. They do not alone establish measured trait role, "
    "outcome, effect direction, causal design, or quantitative eligibility."
)


def read_audit_queue(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = [{key: _text(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    needed = {"audit_group", "route_family_audit", "audit_rank", "candidate_id", "doi", "title"}
    if rows and not needed.issubset(rows[0]):
        raise ValueError("priority-leak audit queue lacks required columns")
    return rows


def _base(row: dict[str, str]) -> dict[str, str]:
    return {field: row.get(field, "") for field in PACKET_FIELDS if field not in {
        "crossref_lookup_status", "crossref_message_type", "crossref_title", "crossref_published_year",
        "crossref_container_title", "crossref_abstract_available", "crossref_abstract_text", "source_packet_warning",
    }}


def _lookup(doi: str, request_json: Callable[[str], dict[str, Any]] | None) -> dict[str, str]:
    if not doi:
        return {
            "crossref_lookup_status": "not_attempted_missing_doi",
            "crossref_message_type": "",
            "crossref_title": "",
            "crossref_published_year": "",
            "crossref_container_title": "",
            "crossref_abstract_available": "false",
            "crossref_abstract_text": "",
            "source_packet_warning": WARNING + " No DOI was available for Crossref lookup.",
        }
    try:
        payload = _request_json(f"{CROSSREF_WORKS_URL}/{quote(doi, safe='')}", request_json)
        message = payload.get("message")
        if not isinstance(message, dict):
            raise ValueError("Crossref response lacks message object")
        abstract = _plain_text(message.get("abstract"))
        return {
            "crossref_lookup_status": "success",
            "crossref_message_type": _text(message.get("type")),
            "crossref_title": _plain_text(message.get("title")),
            "crossref_published_year": _year(message),
            "crossref_container_title": _plain_text(message.get("container-title")),
            "crossref_abstract_available": str(bool(abstract)).lower(),
            "crossref_abstract_text": abstract,
            "source_packet_warning": WARNING,
        }
    except Exception as error:
        return {
            "crossref_lookup_status": "failed",
            "crossref_message_type": "",
            "crossref_title": "",
            "crossref_published_year": "",
            "crossref_container_title": "",
            "crossref_abstract_available": "false",
            "crossref_abstract_text": "",
            "source_packet_warning": WARNING + f" Lookup failed: {type(error).__name__}: {error}",
        }


def build_audit_abstract_packet(
    audit_rows: Iterable[dict[str, str]], *, request_json: Callable[[str], dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Retrieve each DOI once while retaining all audit-route rows in output."""
    cache: dict[str, dict[str, str]] = {}
    packet: list[dict[str, str]] = []
    for row in audit_rows:
        doi = row.get("doi", "").strip()
        if doi not in cache:
            cache[doi] = _lookup(doi, request_json)
        packet.append({**_base(row), **cache[doi]})
    return packet


def write_audit_abstract_packet(path: str | Path, rows: Iterable[dict[str, str]]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PACKET_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
