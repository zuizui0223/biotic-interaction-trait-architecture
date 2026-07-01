"""Paged Crossref retrieval for the existing broad evidence query registry.

This module preserves the existing query registry and candidate construction.
It only permits a requested depth above Crossref's 1,000-record page limit by
retrieving consecutive score-ranked pages and keeping an auditable per-query
receipt.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Iterable

from .broad_reality_evidence import (
    CROSSREF_WORKS_URL,
    MAX_ROWS_PER_QUERY,
    Candidate,
    _request_json,
    candidate_from_crossref_item,
    merge_candidate,
)

CROSSREF_PAGE_SIZE = 1000
MAX_DEEP_ROWS_PER_QUERY = 5000


def harvest_crossref_paged(
    queries: Iterable[dict[str, str]],
    *,
    rows_per_query: int,
    request_json: Callable[[str, dict[str, str]], dict[str, Any]] = _request_json,
) -> tuple[list[Candidate], list[dict[str, str]]]:
    """Retrieve a fixed total depth per query using Crossref score-ranked pages.

    ``rows_per_query`` means a total requested depth, not the size of a single
    Crossref response. A query stops early only when Crossref returns a short
    page. The receipt records whether the requested depth was reached; reaching
    it is a retrieval cap, not a claim that the provider has no further works.
    """

    if not 1 <= rows_per_query <= MAX_DEEP_ROWS_PER_QUERY:
        raise ValueError(
            f"rows_per_query must be between 1 and {MAX_DEEP_ROWS_PER_QUERY} for paged retrieval"
        )

    candidates: dict[str, Candidate] = {}
    reports: list[dict[str, str]] = []
    for query in queries:
        collected = 0
        pages = 0
        api_total_results = ""
        try:
            while collected < rows_per_query:
                page_rows = min(CROSSREF_PAGE_SIZE, rows_per_query - collected)
                payload = request_json(
                    CROSSREF_WORKS_URL,
                    {
                        "query.bibliographic": query["query_text"],
                        "filter": "type:journal-article",
                        "sort": "score",
                        "order": "desc",
                        "rows": str(page_rows),
                        "offset": str(collected),
                    },
                )
                message = payload.get("message")
                if not isinstance(message, dict):
                    raise ValueError("Crossref response lacks message object")
                items = message.get("items")
                if not isinstance(items, list):
                    raise ValueError("Crossref response lacks items list")
                if not api_total_results:
                    api_total_results = str(message.get("total-results", ""))
                pages += 1
                for local_rank, item in enumerate(items, start=1):
                    if not isinstance(item, dict):
                        continue
                    candidate = candidate_from_crossref_item(item, query, collected + local_rank)
                    if not candidate.title:
                        continue
                    if candidate.candidate_id in candidates:
                        merge_candidate(candidates[candidate.candidate_id], candidate)
                    else:
                        candidates[candidate.candidate_id] = candidate
                collected += len(items)
                if len(items) < page_rows:
                    break
            reports.append({
                "query_id": query["query_id"],
                "route_family": query["route_family"],
                "query_text": query["query_text"],
                "requested_rows": str(rows_per_query),
                "works_returned": str(collected),
                "api_total_results": api_total_results,
                "status": "success",
                "message": (
                    f"pages={pages}; retrieval_cap_reached={str(collected == rows_per_query).lower()}; "
                    f"provider_has_more_than_requested={str(api_total_results.isdigit() and int(api_total_results) > rows_per_query).lower()}"
                ),
            })
        except Exception as error:
            reports.append({
                "query_id": query["query_id"],
                "route_family": query["route_family"],
                "query_text": query["query_text"],
                "requested_rows": str(rows_per_query),
                "works_returned": str(collected),
                "api_total_results": api_total_results,
                "status": "query_failed",
                "message": str(error),
            })

    failed = [row["query_id"] for row in reports if row["status"] != "success"]
    if failed:
        raise RuntimeError("Crossref broad corpus retrieval incomplete: " + ", ".join(failed))
    return sorted(candidates.values(), key=lambda item: (item.title.lower(), item.doi)), reports
