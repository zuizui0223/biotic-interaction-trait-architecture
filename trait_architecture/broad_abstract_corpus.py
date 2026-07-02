"""Retrieve a broad abstract packet without adding literature candidates.

The input is the fixed L1 screened-candidate table.  Only candidate rows already
marked `abstract_available=true` by the original Crossref list response are
looked up.  All other L1 candidates are retained in the packet with an explicit
unavailable state, preserving the discovery denominator.

The packet is for shallow, broad evidence mapping.  A Crossref abstract is never
by itself treated as a measured causal effect, an effect direction, or a model
parameter value.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import quote

from trait_architecture.broad_calibration_abstracts import (
    CROSSREF_WORKS_URL,
    _plain_text,
    _request_json,
    _text,
    _year,
)

PACKET_FIELDS = (
    "candidate_id", "doi", "title", "publication_year", "work_type", "container_title",
    "publisher", "source_queries", "route_families", "shallow_screen_status",
    "harvest_abstract_available", "abstract_retrieval_state", "crossref_lookup_status",
    "crossref_message_type", "crossref_title", "crossref_published_year",
    "crossref_container_title", "crossref_abstract_available", "crossref_abstract_text",
    "source_packet_warning",
)

WARNING = (
    "Crossref abstracts are a broad, shallow evidence-map source only. They do not alone establish measured trait role, "
    "causal design, effect direction, independent study identity, or a calibrated theory parameter."
)


class BroadAbstractPacketError(ValueError):
    """Raised for malformed fixed-corpus candidate inputs."""


def is_true(value: object) -> bool:
    return _text(value).lower() in {"true", "1", "yes", "y"}


def read_screened_candidates(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = [{key: _text(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    required = {"candidate_id", "doi", "title", "abstract_available", "shallow_screen_status"}
    if rows and not required.issubset(rows[0]):
        raise BroadAbstractPacketError("screened candidate table lacks required columns")
    identifiers = [row["candidate_id"] for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise BroadAbstractPacketError("screened candidate IDs must be unique")
    return rows


def _base(row: dict[str, str]) -> dict[str, str]:
    return {
        "candidate_id": row.get("candidate_id", ""),
        "doi": row.get("doi", ""),
        "title": row.get("title", ""),
        "publication_year": row.get("publication_year", ""),
        "work_type": row.get("work_type", ""),
        "container_title": row.get("container_title", ""),
        "publisher": row.get("publisher", ""),
        "source_queries": row.get("source_queries", ""),
        "route_families": row.get("route_families", ""),
        "shallow_screen_status": row.get("shallow_screen_status", ""),
        "harvest_abstract_available": str(is_true(row.get("abstract_available"))).lower(),
        "source_packet_warning": WARNING,
    }


def _not_attempted(base: dict[str, str], state: str, reason: str) -> dict[str, str]:
    return {
        **base,
        "abstract_retrieval_state": state,
        "crossref_lookup_status": "not_attempted",
        "crossref_message_type": "",
        "crossref_title": "",
        "crossref_published_year": "",
        "crossref_container_title": "",
        "crossref_abstract_available": "false",
        "crossref_abstract_text": "",
        "source_packet_warning": WARNING + " " + reason,
    }


def _lookup(doi: str, request_json: Callable[[str], dict[str, Any]] | None) -> dict[str, str]:
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
    }


def build_broad_abstract_packet(
    candidate_rows: Iterable[dict[str, str]], *, request_json: Callable[[str], dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Return one packet row for every fixed L1 candidate, using a DOI cache."""
    cache: dict[str, dict[str, str]] = {}
    packet: list[dict[str, str]] = []
    for row in candidate_rows:
        base = _base(row)
        doi = base["doi"].strip()
        if not is_true(row.get("abstract_available")):
            packet.append(_not_attempted(base, "not_eligible_no_harvest_abstract", "The original fixed-corpus response contained no abstract."))
            continue
        if not doi:
            packet.append(_not_attempted(base, "not_eligible_missing_doi", "No DOI is available for a source-identity lookup."))
            continue
        if doi not in cache:
            try:
                cache[doi] = {
                    "abstract_retrieval_state": "looked_up_from_fixed_candidate_doi",
                    **_lookup(doi, request_json),
                    "source_packet_warning": WARNING,
                }
            except Exception as error:
                cache[doi] = {
                    "abstract_retrieval_state": "lookup_failed",
                    "crossref_lookup_status": "failed",
                    "crossref_message_type": "",
                    "crossref_title": "",
                    "crossref_published_year": "",
                    "crossref_container_title": "",
                    "crossref_abstract_available": "false",
                    "crossref_abstract_text": "",
                    "source_packet_warning": WARNING + f" Lookup failed: {type(error).__name__}: {error}",
                }
        packet.append({**base, **cache[doi]})
    return packet


def write_broad_abstract_packet(path: str | Path, rows: Iterable[dict[str, str]]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PACKET_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
