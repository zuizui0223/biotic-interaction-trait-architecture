"""Verify public access and provenance for the Castilleja source-scout leads.

The source scout may find a publisher PDF link and a Dryad search candidate. This
module tests them conservatively:

* publisher links are fetched only with a small byte range to establish
  unauthenticated accessibility and PDF-like content type;
* the Dryad candidate is inspected as metadata only; it is accepted only after
  an exact normalized title match or an explicit allowed DOI relation.

Neither result reads article tables, downloads an archive, or extracts effects.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


USER_AGENT = "biotic-interaction-trait-architecture castilleja-access-probe/0.1"
MAX_PREFIX_BYTES = 4096
ALLOWED_RELATIONS = frozenset({"issupplementto", "isderivedfrom", "ispartof"})


@dataclass(frozen=True)
class AccessReceipt:
    source_label: str
    source_kind: str
    request_url: str
    final_url: str
    resolution_status: str
    http_status: str
    content_type: str
    prefix_signature: str
    candidate_title: str
    candidate_doi: str
    article_relation: str
    notes: str


RECEIPT_FIELDS = tuple(AccessReceipt.__dataclass_fields__)


def _text(value: object) -> str:
    return str(value or "").strip()


def normalise_doi(value: object) -> str:
    doi = _text(value).lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi.strip()


def normalise_title(value: object) -> str:
    text = _text(value).lower()
    text = re.sub(r"^data\s+from\s*:\s*", "", text)
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _fetch_prefix(url: str, *, timeout: int = 30) -> tuple[int, str, str, bytes]:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/pdf,application/octet-stream,*/*",
            "Range": f"bytes=0-{MAX_PREFIX_BYTES - 1}",
        },
    )
    with urlopen(request, timeout=timeout) as response:  # nosec B310: explicit public source candidate
        status = int(getattr(response, "status", response.getcode()))
        final_url = response.geturl()
        content_type = _text(response.headers.get("Content-Type")).lower()
        return status, final_url, content_type, response.read(MAX_PREFIX_BYTES)


def _fetch_json(url: str, *, timeout: int = 20) -> tuple[int, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed public metadata endpoint
        status = int(getattr(response, "status", response.getcode()))
        return status, json.loads(response.read().decode("utf-8"))


def probe_pdf_link(
    label: str,
    url: str,
    *,
    fetch_prefix: Callable[[str], tuple[int, str, str, bytes]] = _fetch_prefix,
) -> AccessReceipt:
    try:
        status, final_url, content_type, prefix = fetch_prefix(url)
        signature = prefix[:4].decode("latin1", errors="replace")
        is_pdf = prefix.startswith(b"%PDF") or "pdf" in content_type
        return AccessReceipt(
            source_label=label, source_kind="publisher_pdf_candidate", request_url=url,
            final_url=final_url, resolution_status="public_pdf_prefix_recovered" if is_pdf else "non_pdf_content_returned",
            http_status=str(status), content_type=content_type, prefix_signature=signature,
            candidate_title="", candidate_doi="", article_relation="exact_article_link",
            notes=("Unauthenticated byte-range response is PDF-like; full text can now be screened without using credentials."
                   if is_pdf else "Endpoint responded, but the small public response was not PDF-like."),
        )
    except HTTPError as error:
        return AccessReceipt(
            source_label=label, source_kind="publisher_pdf_candidate", request_url=url, final_url="",
            resolution_status="access_denied_or_required", http_status=str(error.code), content_type="",
            prefix_signature="", candidate_title="", candidate_doi="", article_relation="exact_article_link",
            notes=f"HTTPError: {error}",
        )
    except Exception as error:
        return AccessReceipt(
            source_label=label, source_kind="publisher_pdf_candidate", request_url=url, final_url="",
            resolution_status="access_failed", http_status="", content_type="", prefix_signature="",
            candidate_title="", candidate_doi="", article_relation="exact_article_link",
            notes=f"{type(error).__name__}: {error}",
        )


def _candidate_title(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    attrs = payload.get("attributes") if isinstance(payload.get("attributes"), dict) else payload
    return _text(attrs.get("title") or attrs.get("name"))


def _candidate_doi(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    attrs = payload.get("attributes") if isinstance(payload.get("attributes"), dict) else payload
    return normalise_doi(attrs.get("doi") or attrs.get("identifier"))


def _relation_from_datacite(payload: Any, article_doi: str) -> str:
    if not isinstance(payload, dict):
        return ""
    data = payload.get("data")
    attrs = data.get("attributes") if isinstance(data, dict) and isinstance(data.get("attributes"), dict) else {}
    related = attrs.get("relatedIdentifiers") or attrs.get("related_identifiers")
    if not isinstance(related, list):
        return ""
    for item in related:
        if not isinstance(item, dict):
            continue
        target = normalise_doi(item.get("relatedIdentifier") or item.get("identifier"))
        relation = _text(item.get("relationType") or item.get("relation_type"))
        if target == article_doi:
            return relation
    return ""


def probe_dryad_candidate(
    *,
    dataset_id: str,
    article_doi: str,
    article_title: str,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
) -> AccessReceipt:
    article_doi = normalise_doi(article_doi)
    endpoint = f"https://datadryad.org/api/v2/datasets/{quote(_text(dataset_id), safe='')}"
    try:
        status, payload = fetch_json(endpoint)
        if status >= 400:
            raise RuntimeError(f"Dryad HTTP {status}")
        title = _candidate_title(payload)
        doi = _candidate_doi(payload)
        relation = ""
        if doi:
            datacite_url = f"https://api.datacite.org/dois/{quote(doi, safe='')}"
            try:
                dc_status, dc_payload = fetch_json(datacite_url)
                if dc_status < 400:
                    relation = _relation_from_datacite(dc_payload, article_doi)
            except Exception:
                relation = ""
        if relation.lower() in ALLOWED_RELATIONS:
            status_label = "candidate_identity_verified_by_relation"
        elif normalise_title(title) == normalise_title(article_title):
            status_label = "candidate_identity_verified_by_exact_title"
        else:
            status_label = "candidate_identity_unverified"
        return AccessReceipt(
            source_label="Dryad candidate", source_kind="repository_candidate_metadata", request_url=endpoint,
            final_url="", resolution_status=status_label, http_status=str(status), content_type="application/json",
            prefix_signature="", candidate_title=title, candidate_doi=doi, article_relation=relation,
            notes=("Candidate must not be used for effect extraction unless identity is verified."
                   if status_label == "candidate_identity_unverified" else
                   "Candidate identity is verified, but file manifest and table screening remain separate steps."),
        )
    except Exception as error:
        return AccessReceipt(
            source_label="Dryad candidate", source_kind="repository_candidate_metadata", request_url=endpoint,
            final_url="", resolution_status="access_failed", http_status="", content_type="",
            prefix_signature="", candidate_title="", candidate_doi="", article_relation="",
            notes=f"{type(error).__name__}: {error}",
        )


def probe_castilleja_sources(
    *,
    fetch_prefix: Callable[[str], tuple[int, str, str, bytes]] = _fetch_prefix,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
) -> tuple[list[AccessReceipt], dict[str, object]]:
    article_doi = "10.1111/j.0030-1299.2004.12641.x"
    title = "Direct and indirect effects of pollinators and seed predators to selection on plant and floral traits"
    pdf_links = {
        "Wiley TDM": "https://api.wiley.com/onlinelibrary/tdm/v1/articles/10.1111%2Fj.0030-1299.2004.12641.x",
        "Wiley PDF": "https://nsojournals.onlinelibrary.wiley.com/doi/pdf/10.1111/j.0030-1299.2004.12641.x",
    }
    receipts = [probe_pdf_link(label, url, fetch_prefix=fetch_prefix) for label, url in pdf_links.items()]
    receipts.append(probe_dryad_candidate(
        dataset_id="114507", article_doi=article_doi, article_title=title, fetch_json=fetch_json,
    ))
    labels = sorted({receipt.resolution_status for receipt in receipts})
    return receipts, {
        "study_doi": article_doi,
        "receipt_count": len(receipts),
        "counts_by_status": {label: sum(row.resolution_status == label for row in receipts) for label in labels},
        "full_text_screen_allowed": any(row.resolution_status == "public_pdf_prefix_recovered" for row in receipts),
        "verified_repository_candidate": any(
            row.resolution_status.startswith("candidate_identity_verified") for row in receipts
        ),
        "decision_boundary": "Access verification does not read the paper, establish trait functions, or extract reported coefficients.",
    }


def write_probe(out_dir: str | Path, receipts: Iterable[AccessReceipt], report: dict[str, object]) -> None:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "castilleja_access_probe_receipts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RECEIPT_FIELDS)
        writer.writeheader()
        for receipt in receipts:
            writer.writerow(asdict(receipt))
    (output / "castilleja_access_probe_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )