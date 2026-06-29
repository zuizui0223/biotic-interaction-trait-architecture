"""Create an auditable receipt for a public Dryad dataset without retaining raw data.

The script retrieves Dryad metadata, follows the dataset's own version/file API
links, and records file inventory plus headers for small public tabular files.
It never classifies a study as M1/M2/D1 and does not commit raw observations.

Usage:
    python scripts/probe_dryad_public_dataset.py 10.5061/dryad.0j96d17 artifacts/impatiens_dryad_probe
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections import deque
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urljoin, urlparse
from urllib.request import Request, urlopen


DRYAD_ORIGIN = "https://datadryad.org"
DRYAD_API = f"{DRYAD_ORIGIN}/api/v2"
USER_AGENT = "biotic-interaction-trait-architecture Dryad public-data probe/0.2 (+https://github.com/zuizui0223/biotic-interaction-trait-architecture)"
MAX_JSON_REQUESTS = 24
MAX_PREVIEW_BYTES = 2_000_000
TABULAR_SUFFIXES = (".csv", ".tsv", ".tab", ".txt")
FILE_FIELDS = [
    "file_name",
    "file_id",
    "mime_type",
    "size_bytes",
    "metadata_url",
    "download_url",
    "tabular_candidate",
    "preview_status",
    "detected_delimiter",
    "header_columns",
    "first_data_row_column_count",
]


def text(value: object) -> str:
    return str(value or "").strip()


def normalise_doi(value: object) -> str:
    raw = unquote(text(value)).lower()
    if "doi.org/" in raw:
        raw = raw.split("doi.org/", 1)[1]
    return raw.removeprefix("doi:").split("?", 1)[0].split("#", 1)[0].strip().strip(".,; ")


def absolute_dryad_url(value: object, base_url: str = DRYAD_ORIGIN) -> str:
    raw = text(value)
    if not raw:
        return ""
    return urljoin(base_url, raw)


def request_json(url: str, timeout: float) -> tuple[str, Any | None]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310: public Dryad API only
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        return f"http_error_{error.code}", None
    except URLError as error:
        return f"url_error_{type(error.reason).__name__}", None
    except TimeoutError:
        return "timeout", None
    except Exception as error:
        return f"error_{type(error).__name__}", None
    return "success", payload


def request_bytes(url: str, timeout: float, max_bytes: int) -> tuple[str, bytes]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Range": f"bytes=0-{max_bytes - 1}"})
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310: public files directly linked by Dryad API
            return "success", response.read(max_bytes)
    except HTTPError as error:
        return f"http_error_{error.code}", b""
    except URLError as error:
        return f"url_error_{type(error.reason).__name__}", b""
    except TimeoutError:
        return "timeout", b""
    except Exception as error:
        return f"error_{type(error).__name__}", b""


def link_urls(value: object, base_url: str) -> list[tuple[str, str]]:
    """Recursively retain labelled API URLs, including Dryad's relative hrefs."""
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(child, str) and child.startswith(("/api/v2/", "https://datadryad.org/api/v2/")):
                found.append((str(key), absolute_dryad_url(child, base_url)))
            elif isinstance(child, dict):
                href = child.get("href") or child.get("url")
                if isinstance(href, str) and href.startswith(("/api/v2/", "https://datadryad.org/api/v2/")):
                    found.append((str(key), absolute_dryad_url(href, base_url)))
            found.extend(link_urls(child, base_url))
    elif isinstance(value, list):
        for child in value:
            found.extend(link_urls(child, base_url))
    return found


def looks_like_dryad_api(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname == "datadryad.org" and "/api/v2/" in parsed.path


def _download_link(links: object, metadata_url: str) -> str:
    if not isinstance(links, dict):
        return ""
    raw = links.get("stash:download") or links.get("download")
    if isinstance(raw, dict):
        raw = raw.get("href") or raw.get("url")
    return absolute_dryad_url(raw, metadata_url)


def _file_record_from_object(obj: dict[str, Any], metadata_url: str) -> dict[str, str] | None:
    attributes = obj.get("attributes") if isinstance(obj.get("attributes"), dict) else obj
    if not isinstance(attributes, dict):
        return None
    candidate_name = text(
        attributes.get("path")
        or attributes.get("fileName")
        or attributes.get("filename")
        or attributes.get("name")
        or attributes.get("original_filename")
    )
    links = obj.get("links") if isinstance(obj.get("links"), dict) else obj.get("_links")
    download_url = text(
        attributes.get("downloadUrl")
        or attributes.get("download_url")
        or _download_link(links, metadata_url)
    )
    file_id = text(obj.get("id") or attributes.get("id"))
    mime_type = text(attributes.get("mimeType") or attributes.get("mime_type") or attributes.get("contentType"))
    size = attributes.get("size") or attributes.get("sizeBytes") or attributes.get("size_bytes")
    if not candidate_name and not download_url:
        return None
    if not candidate_name:
        candidate_name = urlparse(download_url).path.rsplit("/", 1)[-1] or file_id
    return {
        "file_name": candidate_name,
        "file_id": file_id,
        "mime_type": mime_type,
        "size_bytes": text(size),
        "metadata_url": metadata_url,
        "download_url": download_url,
        "tabular_candidate": str(candidate_name.lower().endswith(TABULAR_SUFFIXES)).lower(),
        "preview_status": "not_attempted",
        "detected_delimiter": "",
        "header_columns": "",
        "first_data_row_column_count": "",
    }


def objects_from_json(payload: object) -> Iterable[dict[str, Any]]:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list):
            yield from (item for item in data if isinstance(item, dict))
        elif isinstance(data, dict):
            yield data
        for key in ("included", "files", "items", "_embedded"):
            nested = payload.get(key)
            if isinstance(nested, list):
                yield from (item for item in nested if isinstance(item, dict))
            elif isinstance(nested, dict):
                yield nested
    elif isinstance(payload, list):
        yield from (item for item in payload if isinstance(item, dict))


def discover_dryad_document_tree(
    dataset_doi: str, timeout: float
) -> tuple[dict[str, Any], list[tuple[str, object]], list[dict[str, str]]]:
    root = f"{DRYAD_API}/datasets/doi:{quote(dataset_doi, safe='')}"
    queue: deque[str] = deque([root])
    visited: set[str] = set()
    documents: list[tuple[str, object]] = []
    inventory: dict[tuple[str, str], dict[str, str]] = {}
    root_payload: dict[str, Any] = {}

    while queue and len(visited) < MAX_JSON_REQUESTS:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        status, payload = request_json(url, timeout)
        documents.append((url, {"status": status, "payload": payload}))
        if status != "success" or payload is None:
            continue
        if url == root and isinstance(payload, dict):
            root_payload = payload

        for obj in objects_from_json(payload):
            record = _file_record_from_object(obj, url)
            if record:
                inventory.setdefault((record["file_id"], record["file_name"]), record)

        for key, link in link_urls(payload, url):
            if looks_like_dryad_api(link):
                label = key.lower()
                if any(token in label for token in ("file", "version", "dataset", "related")):
                    queue.append(link)

    return root_payload, documents, list(inventory.values())


def detect_delimiter(sample: str) -> str:
    first_line = next((line for line in sample.splitlines() if line.strip()), "")
    candidates = [("\t", first_line.count("\t")), (",", first_line.count(",")), (";", first_line.count(";"))]
    delimiter, count = max(candidates, key=lambda item: item[1])
    return delimiter if count > 0 else ","


def preview_tabular_file(record: dict[str, str], timeout: float) -> dict[str, str]:
    if record["tabular_candidate"] != "true":
        return record
    if not record["download_url"]:
        record["preview_status"] = "no_direct_download_url"
        return record
    status, payload = request_bytes(record["download_url"], timeout, MAX_PREVIEW_BYTES)
    if status != "success":
        record["preview_status"] = status
        return record
    sample = payload.decode("utf-8-sig", errors="replace")
    delimiter = detect_delimiter(sample)
    try:
        reader = csv.reader(io.StringIO(sample), delimiter=delimiter)
        header = next(reader, [])
        first = next(reader, [])
    except csv.Error as error:
        record["preview_status"] = f"csv_error_{type(error).__name__}"
        return record
    record["preview_status"] = "header_previewed"
    record["detected_delimiter"] = "tab" if delimiter == "\t" else delimiter
    record["header_columns"] = ";".join(header)
    record["first_data_row_column_count"] = str(len(first))
    return record


def write_csv(path: Path, rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FILE_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FILE_FIELDS})


def dataset_title(payload: dict[str, Any]) -> str:
    if text(payload.get("title")):
        return text(payload.get("title"))
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    attributes = data.get("attributes") if isinstance(data.get("attributes"), dict) else {}
    return text(attributes.get("title"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_doi")
    parser.add_argument("out_dir")
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args(argv)
    dataset_doi = normalise_doi(args.dataset_doi)
    if not dataset_doi:
        raise SystemExit("dataset DOI is required")
    if args.timeout_seconds <= 0:
        raise SystemExit("timeout must be positive")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    root_payload, documents, inventory = discover_dryad_document_tree(dataset_doi, args.timeout_seconds)
    inventory = [preview_tabular_file(record, args.timeout_seconds) for record in inventory]
    (out_dir / "dryad_dataset_metadata.json").write_text(json.dumps(root_payload, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "dryad_api_receipt.json").write_text(
        json.dumps(
            {
                "dataset_doi": dataset_doi,
                "dataset_title": dataset_title(root_payload),
                "api_documents_visited": [
                    {"url": url, "status": body.get("status") if isinstance(body, dict) else "unknown"}
                    for url, body in documents
                ],
                "file_inventory_count": len(inventory),
                "tabular_previewed_count": sum(item["preview_status"] == "header_previewed" for item in inventory),
                "warning": "This receipt inventories public files and headers only. It does not establish the biological linkage or D1 eligibility.",
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    write_csv(out_dir / "dryad_file_inventory.csv", inventory)
    print(json.dumps({"dataset_doi": dataset_doi, "title": dataset_title(root_payload), "files": len(inventory)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
