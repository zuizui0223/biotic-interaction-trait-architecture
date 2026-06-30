"""Scout public article and repository sources without conflating their provenance.

A study DOI can have several different public traces:

* article metadata;
* a publisher content or text-mining link;
* an open-access full-text location;
* a linked repository record; or
* no recoverable source at a particular endpoint.

They are intentionally emitted as separate receipts. A discovered dataset must
not be treated as the article's original data unless its relationship is explicit,
and a public full-text candidate must not be treated as a recoverable effect table
until the file contents are screened.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import quote
from urllib.request import Request, urlopen

from .public_repository_resolver import RepositoryReceipt, resolve_row


USER_AGENT = "biotic-interaction-trait-architecture public-article-source-scout/0.1"


@dataclass(frozen=True)
class ArticleSourceReceipt:
    study_doi: str
    provider: str
    source_kind: str
    resolution_status: str
    request_url: str
    source_identifier: str
    title: str
    landing_page_url: str
    content_url: str
    content_type: str
    license_label: str
    relation_to_article: str
    notes: str


ARTICLE_RECEIPT_FIELDS = tuple(ArticleSourceReceipt.__dataclass_fields__)


def _text(value: object) -> str:
    return str(value or "").strip()


def normalise_doi(value: object) -> str:
    doi = _text(value).lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi.strip()


def _url(value: object) -> str:
    text = _text(value)
    return text if text.startswith(("https://", "http://")) else ""


def _fetch_json(url: str, *, timeout: int = 20) -> tuple[int, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed public metadata endpoints
        status = int(getattr(response, "status", response.getcode()))
        return status, json.loads(response.read().decode("utf-8"))


def _first_title(value: object) -> str:
    if isinstance(value, list):
        for item in value:
            if _text(item):
                return _text(item)
    return _text(value)


def _license_label(value: object) -> str:
    if isinstance(value, list):
        labels = []
        for item in value:
            if isinstance(item, dict):
                labels.append(_text(item.get("URL") or item.get("url") or item.get("content-version")))
        return ";".join(label for label in labels if label)
    if isinstance(value, dict):
        return _text(value.get("license") or value.get("url"))
    return _text(value)


def crossref_receipts(
    doi: str,
    *,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
) -> list[ArticleSourceReceipt]:
    doi = normalise_doi(doi)
    url = f"https://api.crossref.org/works/{quote(doi, safe='')}"
    try:
        status, payload = fetch_json(url)
        if status >= 400 or not isinstance(payload, dict) or not isinstance(payload.get("message"), dict):
            raise RuntimeError(f"HTTP {status}")
        message = payload["message"]
        title = _first_title(message.get("title"))
        landing = _url(message.get("URL")) or f"https://doi.org/{doi}"
        license_label = _license_label(message.get("license"))
        receipts = [ArticleSourceReceipt(
            study_doi=doi, provider="Crossref", source_kind="article_metadata",
            resolution_status="metadata_recovered", request_url=url,
            source_identifier=_text(message.get("DOI")) or doi, title=title,
            landing_page_url=landing, content_url="", content_type="", license_label=license_label,
            relation_to_article="exact_article_doi",
            notes="Exact DOI metadata recovered. Metadata alone does not establish full-text or table access.",
        )]
        seen: set[tuple[str, str]] = set()
        for link in message.get("link") or []:
            if not isinstance(link, dict):
                continue
            content = _url(link.get("URL"))
            if not content or (content, _text(link.get("content-type"))) in seen:
                continue
            seen.add((content, _text(link.get("content-type"))))
            receipts.append(ArticleSourceReceipt(
                study_doi=doi, provider="Crossref", source_kind="publisher_content_link",
                resolution_status="content_link_discovered", request_url=url,
                source_identifier=_text(message.get("DOI")) or doi, title=title,
                landing_page_url=landing, content_url=content,
                content_type=_text(link.get("content-type")), license_label=license_label,
                relation_to_article="exact_article_doi",
                notes="Publisher content/text-mining link discovered. Accessibility and table contents remain untested.",
            ))
        return receipts
    except Exception as error:
        return [ArticleSourceReceipt(
            study_doi=doi, provider="Crossref", source_kind="article_metadata",
            resolution_status="access_failed", request_url=url, source_identifier="", title="",
            landing_page_url="", content_url="", content_type="", license_label="",
            relation_to_article="not_checked", notes=f"{type(error).__name__}: {error}",
        )]


def _openalex_locations(payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    best = payload.get("best_oa_location")
    if isinstance(best, dict):
        yield best
    for location in payload.get("locations") or []:
        if isinstance(location, dict):
            yield location


def openalex_receipts(
    doi: str,
    *,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
) -> list[ArticleSourceReceipt]:
    doi = normalise_doi(doi)
    url = f"https://api.openalex.org/works/{quote(f'https://doi.org/{doi}', safe=':/')}"
    try:
        status, payload = fetch_json(url)
        if status >= 400 or not isinstance(payload, dict):
            raise RuntimeError(f"HTTP {status}")
        title = _text(payload.get("title"))
        identifier = _text(payload.get("id"))
        oa = payload.get("open_access") if isinstance(payload.get("open_access"), dict) else {}
        is_oa = bool(oa.get("is_oa"))
        receipts: list[ArticleSourceReceipt] = []
        seen: set[str] = set()
        for location in _openalex_locations(payload):
            pdf = _url(location.get("pdf_url"))
            landing = _url(location.get("landing_page_url"))
            if not pdf and not (is_oa and landing):
                continue
            candidate = pdf or landing
            if candidate in seen:
                continue
            seen.add(candidate)
            source = location.get("source") if isinstance(location.get("source"), dict) else {}
            receipts.append(ArticleSourceReceipt(
                study_doi=doi, provider="OpenAlex", source_kind="open_access_location",
                resolution_status="public_fulltext_candidate" if pdf else "public_landing_candidate",
                request_url=url, source_identifier=identifier, title=title,
                landing_page_url=landing, content_url=pdf,
                content_type="application/pdf" if pdf else "", license_label=_text(location.get("license")),
                relation_to_article="exact_article_doi",
                notes=("OpenAlex identifies a public PDF candidate. Accessibility and table contents remain untested."
                       if pdf else "OpenAlex identifies an OA landing-page candidate but no PDF URL."),
            ))
        if not receipts:
            receipts.append(ArticleSourceReceipt(
                study_doi=doi, provider="OpenAlex", source_kind="open_access_location",
                resolution_status="not_found", request_url=url, source_identifier=identifier, title=title,
                landing_page_url="", content_url="", content_type="", license_label="",
                relation_to_article="exact_article_doi",
                notes="No public full-text location was returned for the exact DOI.",
            ))
        return receipts
    except Exception as error:
        return [ArticleSourceReceipt(
            study_doi=doi, provider="OpenAlex", source_kind="open_access_location",
            resolution_status="access_failed", request_url=url, source_identifier="", title="",
            landing_page_url="", content_url="", content_type="", license_label="",
            relation_to_article="not_checked", notes=f"{type(error).__name__}: {error}",
        )]


def repository_as_article_receipts(repository_rows: Iterable[RepositoryReceipt]) -> list[ArticleSourceReceipt]:
    receipts: list[ArticleSourceReceipt] = []
    for row in repository_rows:
        status = {
            "manifest_recovered": "linked_repository_manifest",
            "landing_page_only": "linked_repository_candidate",
            "not_found": "not_found",
            "access_failed": "access_failed",
        }.get(row.resolution_status, row.resolution_status)
        receipts.append(ArticleSourceReceipt(
            study_doi=row.study_doi, provider=row.repository, source_kind="linked_repository",
            resolution_status=status, request_url=row.request_url, source_identifier=row.dataset_identifier,
            title="", landing_page_url=row.landing_page_url, content_url=row.file_url,
            content_type="", license_label="", relation_to_article="endpoint_screen_only",
            notes=row.notes,
        ))
    return receipts


def audit_study_sources(
    *,
    study_doi: str,
    queue_id: str,
    study_id: str,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
) -> tuple[list[ArticleSourceReceipt], dict[str, object]]:
    doi = normalise_doi(study_doi)
    article = [*crossref_receipts(doi, fetch_json=fetch_json), *openalex_receipts(doi, fetch_json=fetch_json)]
    repository_row = {
        "queue_id": queue_id,
        "study_id": study_id,
        "citation_or_doi": doi,
        "queue_status": "queued",
    }
    repositories = repository_as_article_receipts(resolve_row(repository_row, fetch_json=fetch_json))
    receipts = article + repositories
    labels = sorted({receipt.resolution_status for receipt in receipts})
    report = {
        "study_doi": doi,
        "receipt_count": len(receipts),
        "counts_by_status": {label: sum(row.resolution_status == label for row in receipts) for label in labels},
        "has_public_pdf_candidate": any(
            row.resolution_status == "public_fulltext_candidate" and bool(row.content_url)
            for row in receipts
        ),
        "has_linked_repository_manifest": any(
            row.resolution_status == "linked_repository_manifest" for row in receipts
        ),
        "decision_boundary": (
            "This source scout identifies where a public full text or dataset may be reachable. "
            "It does not read article tables, evaluate trait function, estimate effects, or assign D1/D2/D3."
        ),
    }
    return receipts, report


def write_audit(out_dir: str | Path, receipts: Iterable[ArticleSourceReceipt], report: dict[str, object]) -> None:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "public_article_source_receipts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ARTICLE_RECEIPT_FIELDS)
        writer.writeheader()
        for receipt in receipts:
            writer.writerow(asdict(receipt))
    (output / "public_article_source_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
