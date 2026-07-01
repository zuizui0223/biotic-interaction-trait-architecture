"""Retrieve source metadata abstracts for a pinned broad calibration batch.

The packet is a source-screening aid. Abstract text is not automatically coded as
a measured trait, causal effect, or direction. It provides the accessible source
basis needed for the calibration batch to make explicit inclusion/exclusion
judgments before any bulk coding.
"""

from __future__ import annotations

import csv
import html
import json
import re
import time
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


CROSSREF_WORKS_URL = "https://api.crossref.org/works"
USER_AGENT = "biotic-interaction-trait-architecture broad-calibration-abstracts/0.1"
REQUEST_INTERVAL_SECONDS = 0.35
MAX_RETRIES = 3
RETRYABLE_HTTP_CODES = frozenset({408, 429, 500, 502, 503, 504})
PACKET_FIELDS = (
    "queue_rank", "candidate_id", "doi", "title", "focus_route_families",
    "all_discovery_route_families", "crossref_lookup_status", "crossref_message_type",
    "crossref_title", "crossref_published_year", "crossref_container_title",
    "crossref_abstract_available", "crossref_abstract_text", "source_packet_warning",
)
_last_request_at = 0.0


def _text(value: object) -> str:
    if isinstance(value, list):
        return " ".join(_text(item) for item in value)
    return str(value or "").strip()


def _plain_text(value: object) -> str:
    text = html.unescape(_text(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([,.;:!?])", r"\1", text)


def _year(message: dict[str, Any]) -> str:
    for key in ("published-print", "published-online", "issued", "created"):
        date = message.get(key)
        if not isinstance(date, dict):
            continue
        parts = date.get("date-parts")
        if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
            return _text(parts[0][0])
    return ""


def _request_json(url: str, request_json: Callable[[str], dict[str, Any]] | None = None) -> dict[str, Any]:
    if request_json is not None:
        return request_json(url)
    global _last_request_at
    for attempt in range(MAX_RETRIES + 1):
        wait = REQUEST_INTERVAL_SECONDS - (time.monotonic() - _last_request_at)
        if wait > 0:
            time.sleep(wait)
        request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=90) as response:  # nosec B310: fixed public Crossref endpoint
                _last_request_at = time.monotonic()
                payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Crossref response is not a JSON object")
            return payload
        except HTTPError as error:
            _last_request_at = time.monotonic()
            if error.code not in RETRYABLE_HTTP_CODES or attempt >= MAX_RETRIES:
                raise
            time.sleep(max(REQUEST_INTERVAL_SECONDS, 2 ** attempt))
        except URLError:
            _last_request_at = time.monotonic()
            if attempt >= MAX_RETRIES:
                raise
            time.sleep(max(REQUEST_INTERVAL_SECONDS, 2 ** attempt))
    raise RuntimeError("unreachable retry termination")


def read_calibration_batch(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = [{key: _text(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    needed = {"queue_rank", "candidate_id", "doi", "title", "focus_route_families", "all_discovery_route_families"}
    if rows and not needed.issubset(rows[0]):
        raise ValueError("calibration batch lacks required columns")
    if any(not row["doi"] for row in rows):
        raise ValueError("calibration abstract packet requires DOI-backed candidates")
    return rows


def build_abstract_packet(
    batch_rows: Iterable[dict[str, str]],
    *,
    request_json: Callable[[str], dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Retrieve one Crossref message per calibration DOI; preserve failed lookups."""

    packet: list[dict[str, str]] = []
    for row in batch_rows:
        doi = row["doi"]
        url = f"{CROSSREF_WORKS_URL}/{quote(doi, safe='')}"
        base = {
            "queue_rank": row["queue_rank"],
            "candidate_id": row["candidate_id"],
            "doi": doi,
            "title": row["title"],
            "focus_route_families": row["focus_route_families"],
            "all_discovery_route_families": row["all_discovery_route_families"],
            "source_packet_warning": (
                "Crossref metadata abstracts support source screening only. They do not alone establish measured trait role, "
                "outcome, effect direction, causal design, or quantitative eligibility."
            ),
        }
        try:
            payload = _request_json(url, request_json)
            message = payload.get("message")
            if not isinstance(message, dict):
                raise ValueError("Crossref response lacks message object")
            abstract = _plain_text(message.get("abstract"))
            packet.append({
                **base,
                "crossref_lookup_status": "success",
                "crossref_message_type": _text(message.get("type")),
                "crossref_title": _plain_text(message.get("title")),
                "crossref_published_year": _year(message),
                "crossref_container_title": _plain_text(message.get("container-title")),
                "crossref_abstract_available": str(bool(abstract)).lower(),
                "crossref_abstract_text": abstract,
            })
        except Exception as error:
            packet.append({
                **base,
                "crossref_lookup_status": "failed",
                "crossref_message_type": "",
                "crossref_title": "",
                "crossref_published_year": "",
                "crossref_container_title": "",
                "crossref_abstract_available": "false",
                "crossref_abstract_text": "",
                "source_packet_warning": base["source_packet_warning"] + f" Lookup failed: {type(error).__name__}: {error}",
            })
    return packet


def write_abstract_packet(path: str | Path, rows: Iterable[dict[str, str]]) -> None:
    rows = list(rows)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PACKET_FIELDS)
        writer.writeheader()
        writer.writerows(rows)