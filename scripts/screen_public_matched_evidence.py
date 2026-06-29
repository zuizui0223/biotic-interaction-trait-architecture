"""Screen every matched-flower seed for discoverable public evidence resources.

This is a discovery-and-triage script, not an evidence classifier. It keeps the
entire harvested candidate universe and asks only whether public machine-readable
resources can be *positively discovered* through linked OpenAlex metadata,
public landing-page links, and DataCite DOI relations.

Absence of a discovered link never means that a supplement, repository, or raw
data do not exist. A D1/M2/M1 classification still requires full-text and table
screening under ``MATCHED_STUDY_PROTOCOL.md``.

Usage:
    python scripts/screen_public_matched_evidence.py \
      openalex_matched_flower_all_candidates.csv \
      artifacts/public_evidence_screen

No third-party Python dependency is required.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, unquote, urljoin, urlparse
from urllib.request import Request, urlopen


DATACITE_DOIS_URL = "https://api.datacite.org/dois"
USER_AGENT = "biotic-interaction-trait-architecture public-evidence screen/0.1 (+https://github.com/zuizui0223/biotic-interaction-trait-architecture)"

REPOSITORY_HOST_FRAGMENTS = (
    "datadryad.org",
    "dryad.org",
    "zenodo.org",
    "figshare.com",
    "osf.io",
    "dataverse",
    "data.mendeley.com",
    "github.com",
    "giga-db.org",
    "pangaea.de",
    "edmond.mpdl.mpg.de",
    "b2share",
)
SUPPLEMENT_TERMS = (
    "supplement",
    "supporting information",
    "supporting-information",
    "supplementary",
    "appendix",
    "additional file",
    "data availability",
)
MACHINE_READABLE_SUFFIXES = (
    ".csv",
    ".tsv",
    ".tab",
    ".xlsx",
    ".xls",
    ".zip",
    ".rds",
    ".rdata",
    ".json",
    ".xml",
)
DATASET_RESOURCE_TYPES = frozenset({"dataset", "collection", "software"})

INPUT_REQUIRED_COLUMNS = {
    "candidate_id",
    "seed_routes",
    "seed_query_ids",
    "title",
    "doi",
    "landing_page_url",
    "open_access_url",
    "is_open_access",
    "metadata_match_score",
    "metadata_attraction_signal",
    "metadata_barrier_signal",
    "metadata_pollination_signal",
    "metadata_antagonist_signal",
    "metadata_recoverability_signal",
}

OUTPUT_FIELDS = [
    "candidate_id",
    "seed_routes",
    "seed_query_ids",
    "title",
    "doi",
    "publication_year",
    "authors",
    "is_open_access",
    "open_access_url",
    "landing_page_url",
    "metadata_match_score",
    "metadata_attraction_signal",
    "metadata_barrier_signal",
    "metadata_pollination_signal",
    "metadata_antagonist_signal",
    "metadata_recoverability_signal",
    "openalex_public_full_text_status",
    "known_repository_from_metadata",
    "landing_page_discovery_status",
    "supplement_link_count",
    "supplement_urls",
    "machine_readable_link_count",
    "machine_readable_urls",
    "repository_link_count",
    "repository_urls",
    "datacite_query_status",
    "datacite_related_dataset_count",
    "datacite_related_dataset_dois",
    "datacite_related_dataset_urls",
    "public_evidence_priority_score",
    "public_evidence_action",
    "automatic_evidence_level",
    "automatic_screen_warning",
]


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._current_href: str | None = None
        self._current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self._current_href = href
            self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._current_href is not None:
            self.links.append((self._current_href, " ".join(self._current_text).strip()))
            self._current_href = None
            self._current_text = []


def text(value: object) -> str:
    return str(value or "").strip()


def truthy(value: object) -> bool:
    return text(value).lower() in {"1", "true", "yes", "y"}


def normalise_doi(value: object) -> str:
    raw = unquote(text(value)).lower()
    if not raw:
        return ""
    if "doi.org/" in raw:
        raw = raw.split("doi.org/", 1)[1]
    raw = raw.removeprefix("doi:")
    raw = raw.split("?", 1)[0].split("#", 1)[0]
    return raw.strip().strip(".,; ")


def host_of(url: object) -> str:
    return (urlparse(text(url)).hostname or "").lower()


def is_repository_url(url: object) -> bool:
    host = host_of(url)
    return bool(host) and any(fragment in host for fragment in REPOSITORY_HOST_FRAGMENTS)


def is_machine_readable_url(url: object) -> bool:
    return urlparse(text(url)).path.lower().endswith(MACHINE_READABLE_SUFFIXES)


def contains_supplement_signal(url: object, label: object) -> bool:
    signal = f"{text(url)} {text(label)}".lower()
    return any(term in signal for term in SUPPLEMENT_TERMS)


def unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        clean = text(value)
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result


def metadata_full_text_status(row: dict[str, str]) -> str:
    if text(row.get("open_access_url")):
        return "openalex_linked_oa_url"
    if truthy(row.get("is_open_access")):
        return "openalex_oa_flag_without_usable_url"
    return "no_openalex_oa_url"


def choose_landing_page(row: dict[str, str]) -> str:
    landing = text(row.get("landing_page_url"))
    if landing:
        return landing
    oa_url = text(row.get("open_access_url"))
    if oa_url and not urlparse(oa_url).path.lower().endswith(".pdf"):
        return oa_url
    doi = normalise_doi(row.get("doi"))
    return f"https://doi.org/{doi}" if doi else ""


def fetch_html_links(url: str, timeout_seconds: float) -> tuple[str, list[tuple[str, str]], str]:
    """Fetch one public HTML page; never download a PDF, supplement, or data file."""
    if not url:
        return "not_attempted_no_landing_page", [], ""
    request = Request(url, headers={"Accept": "text/html,application/xhtml+xml", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # nosec B310: fixed public landing pages
            content_type = text(response.headers.get("Content-Type")).lower()
            final_url = response.geturl()
            if "html" not in content_type:
                return "non_html_response", [], final_url
            payload = response.read(1_500_000).decode("utf-8", errors="replace")
    except HTTPError as error:
        return f"http_error_{error.code}", [], ""
    except URLError as error:
        return f"url_error_{type(error.reason).__name__}", [], ""
    except TimeoutError:
        return "timeout", [], ""
    except Exception as error:
        return f"fetch_error_{type(error).__name__}", [], ""

    parser = LinkCollector()
    parser.feed(payload)
    return "fetched_html", [(urljoin(final_url, href), label) for href, label in parser.links], final_url


def extract_page_resources(links: Iterable[tuple[str, str]]) -> tuple[list[str], list[str], list[str]]:
    supplements: list[str] = []
    machine: list[str] = []
    repositories: list[str] = []
    for url, label in links:
        if contains_supplement_signal(url, label):
            supplements.append(url)
        if is_machine_readable_url(url):
            machine.append(url)
        if is_repository_url(url):
            repositories.append(url)
    return unique(supplements), unique(machine), unique(repositories)


def datacite_related_datasets(payload: dict[str, Any], article_doi: str) -> list[dict[str, str]]:
    """Return only Dataset/Collection/Software DOI records explicitly linked to the article DOI."""
    results: list[dict[str, str]] = []
    data = payload.get("data")
    for item in data if isinstance(data, list) else []:
        if not isinstance(item, dict) or not isinstance(item.get("attributes"), dict):
            continue
        attributes = item["attributes"]
        resource_type = text((attributes.get("types") or {}).get("resourceTypeGeneral")).lower() if isinstance(attributes.get("types"), dict) else ""
        dataset_doi = normalise_doi(attributes.get("doi"))
        if resource_type not in DATASET_RESOURCE_TYPES or not dataset_doi or dataset_doi == article_doi:
            continue
        related = attributes.get("relatedIdentifiers")
        relation_types = [
            text(relation.get("relationType"))
            for relation in related if isinstance(related, list)
            for relation in [relation]
            if isinstance(relation, dict) and normalise_doi(relation.get("relatedIdentifier")) == article_doi
        ]
        if relation_types:
            results.append(
                {
                    "doi": dataset_doi,
                    "url": text(attributes.get("url")) or f"https://doi.org/{dataset_doi}",
                    "relation_types": ";".join(unique(relation_types)),
                }
            )
    return results


def query_datacite(article_doi: str, timeout_seconds: float) -> tuple[str, list[dict[str, str]]]:
    if not article_doi:
        return "not_attempted_no_doi", []
    request = Request(
        f"{DATACITE_DOIS_URL}?{urlencode({'query': article_doi, 'page[size]': '25'})}",
        headers={"Accept": "application/vnd.api+json", "User-Agent": USER_AGENT},
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # nosec B310: fixed public DataCite API
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        return f"http_error_{error.code}", []
    except URLError as error:
        return f"url_error_{type(error.reason).__name__}", []
    except TimeoutError:
        return "timeout", []
    except Exception as error:
        return f"query_error_{type(error).__name__}", []
    return ("queried", datacite_related_datasets(payload, article_doi)) if isinstance(payload, dict) else ("unexpected_payload", [])


def public_evidence_action(oa_status: str, supplements: list[str], machine: list[str], repositories: list[str], datasets: list[dict[str, str]]) -> str:
    if datasets or machine:
        return "retrieve_public_table_then_full_text_screen"
    if repositories or supplements:
        return "inspect_public_repository_or_supplement_then_full_text_screen"
    if oa_status.startswith("openalex_"):
        return "inspect_open_full_text_for_embedded_supplement_or_data_statement"
    return "retain_in_search_universe_check_access_manually_before_exclusion"


def priority_score(row: dict[str, str], datasets: list[dict[str, str]], supplements: list[str], machine: list[str], repositories: list[str]) -> int:
    score = int(text(row.get("metadata_match_score")) or 0) * 10
    if truthy(row.get("is_open_access")):
        score += 8
    if text(row.get("open_access_url")):
        score += 4
    if is_repository_url(row.get("open_access_url")) or is_repository_url(row.get("landing_page_url")):
        score += 6
    score += min(3, len(supplements)) * 4
    score += min(3, len(repositories)) * 8
    score += min(3, len(machine)) * 10
    score += min(3, len(datasets)) * 12
    return score


def read_candidates(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    if not rows:
        raise ValueError("candidate CSV is empty")
    missing = sorted(INPUT_REQUIRED_COLUMNS.difference(rows[0]))
    if missing:
        raise ValueError(f"candidate CSV missing required columns: {', '.join(missing)}")
    return rows


def screen_candidates(candidates: Iterable[dict[str, str]], timeout_seconds: float, sleep_seconds: float, fetch_landing_pages: bool) -> tuple[list[dict[str, str]], dict[str, Any]]:
    source_rows = list(candidates)
    output_rows: list[dict[str, str]] = []
    counts = {
        "candidates": 0,
        "openalex_linked_oa_url": 0,
        "landing_page_html_fetched": 0,
        "supplement_link_discovered": 0,
        "machine_readable_link_discovered": 0,
        "repository_link_discovered": 0,
        "datacite_related_dataset_discovered": 0,
        "datacite_query_failed": 0,
    }
    for index, source in enumerate(source_rows, start=1):
        row = {key: text(value) for key, value in source.items()}
        counts["candidates"] += 1
        article_doi = normalise_doi(row.get("doi"))
        oa_status = metadata_full_text_status(row)
        if oa_status == "openalex_linked_oa_url":
            counts["openalex_linked_oa_url"] += 1

        page_status, links = "not_attempted", []
        if fetch_landing_pages and truthy(row.get("is_open_access")):
            page_status, links, _ = fetch_html_links(choose_landing_page(row), timeout_seconds)
            if page_status == "fetched_html":
                counts["landing_page_html_fetched"] += 1
        supplements, machine, repositories = extract_page_resources(links)
        metadata_repository = is_repository_url(row.get("open_access_url")) or is_repository_url(row.get("landing_page_url"))
        if metadata_repository:
            repositories = unique([text(row.get("open_access_url")), text(row.get("landing_page_url")), *repositories])
        if supplements:
            counts["supplement_link_discovered"] += 1
        if machine:
            counts["machine_readable_link_discovered"] += 1
        if repositories:
            counts["repository_link_discovered"] += 1

        datacite_status, datasets = query_datacite(article_doi, timeout_seconds)
        if datacite_status != "queried" and not datacite_status.startswith("not_attempted"):
            counts["datacite_query_failed"] += 1
        if datasets:
            counts["datacite_related_dataset_discovered"] += 1

        output_rows.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "seed_routes": row.get("seed_routes", ""),
                "seed_query_ids": row.get("seed_query_ids", ""),
                "title": row.get("title", ""),
                "doi": article_doi,
                "publication_year": row.get("publication_year", ""),
                "authors": row.get("authors", ""),
                "is_open_access": row.get("is_open_access", ""),
                "open_access_url": row.get("open_access_url", ""),
                "landing_page_url": row.get("landing_page_url", ""),
                "metadata_match_score": row.get("metadata_match_score", ""),
                "metadata_attraction_signal": row.get("metadata_attraction_signal", ""),
                "metadata_barrier_signal": row.get("metadata_barrier_signal", ""),
                "metadata_pollination_signal": row.get("metadata_pollination_signal", ""),
                "metadata_antagonist_signal": row.get("metadata_antagonist_signal", ""),
                "metadata_recoverability_signal": row.get("metadata_recoverability_signal", ""),
                "openalex_public_full_text_status": oa_status,
                "known_repository_from_metadata": str(metadata_repository).lower(),
                "landing_page_discovery_status": page_status,
                "supplement_link_count": str(len(supplements)),
                "supplement_urls": " | ".join(supplements),
                "machine_readable_link_count": str(len(machine)),
                "machine_readable_urls": " | ".join(machine),
                "repository_link_count": str(len(repositories)),
                "repository_urls": " | ".join(repositories),
                "datacite_query_status": datacite_status,
                "datacite_related_dataset_count": str(len(datasets)),
                "datacite_related_dataset_dois": " | ".join(item["doi"] for item in datasets),
                "datacite_related_dataset_urls": " | ".join(item["url"] for item in datasets),
                "public_evidence_priority_score": str(priority_score(row, datasets, supplements, machine, repositories)),
                "public_evidence_action": public_evidence_action(oa_status, supplements, machine, repositories, datasets),
                "automatic_evidence_level": "M0_candidate_needs_full_text",
                "automatic_screen_warning": "Positive link discovery is triage only. No missing link is evidence of no data, and no candidate is automatically D1/M2/M1.",
            }
        )
        if sleep_seconds and index < len(source_rows):
            time.sleep(sleep_seconds)

    report = {
        "source_universe": "all rows from the OpenAlex matched-flower harvest, not a final study set",
        "candidate_count": counts["candidates"],
        "positive_discovery_counts": counts,
        "scope": {
            "openalex": "uses harvested OA flags and linked OA URLs",
            "landing_pages": "fetches at most one public HTML page per OA candidate; does not download PDFs or files",
            "datacite": "looks only for non-article Dataset/Collection/Software DOI records explicitly related to the article DOI",
        },
        "interpretation": [
            "A positive repository, supplement, machine-readable, or DataCite relation is a retrieval lead, not a D1 classification.",
            "A negative or failed discovery does not establish that data are unavailable.",
            "Manual full-text and table screening remains required before M1/M2/D1 assignment.",
        ],
    }
    return output_rows, report


def write_csv(path: Path, rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in OUTPUT_FIELDS})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates_csv")
    parser.add_argument("out_dir")
    parser.add_argument("--timeout-seconds", type=float, default=12.0)
    parser.add_argument("--sleep-seconds", type=float, default=0.15)
    parser.add_argument("--skip-landing-pages", action="store_true")
    args = parser.parse_args(argv)
    if args.timeout_seconds <= 0:
        raise SystemExit("--timeout-seconds must be positive")
    if args.sleep_seconds < 0:
        raise SystemExit("--sleep-seconds cannot be negative")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, report = screen_candidates(
        read_candidates(args.candidates_csv),
        timeout_seconds=args.timeout_seconds,
        sleep_seconds=args.sleep_seconds,
        fetch_landing_pages=not args.skip_landing_pages,
    )
    ranked = sorted(rows, key=lambda row: (-int(row["public_evidence_priority_score"]), row["title"].lower(), row["candidate_id"]))
    leads = [
        row for row in ranked
        if int(row["datacite_related_dataset_count"]) > 0
        or int(row["machine_readable_link_count"]) > 0
        or int(row["repository_link_count"]) > 0
        or int(row["supplement_link_count"]) > 0
    ]
    write_csv(out_dir / "all_candidates_public_evidence_screen.csv", ranked)
    write_csv(out_dir / "public_resource_positive_leads.csv", leads)
    report["ranked_candidate_count"] = len(ranked)
    report["positive_public_resource_lead_count"] = len(leads)
    (out_dir / "public_evidence_screen_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
