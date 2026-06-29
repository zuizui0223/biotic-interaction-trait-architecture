"""Follow the Dryad `stash:version` link and save its endpoint structure.

Usage:
    python scripts/inspect_dryad_version_payload.py 10.5061/dryad.example artifacts/dryad_version
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen


BASE = "https://datadryad.org"
USER_AGENT = "biotic-interaction-trait-architecture dryad-version-inspector/0.1"


def fetch(url: str, timeout: int = 20):
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed public endpoint
        return int(getattr(response, "status", response.getcode())), json.loads(response.read().decode("utf-8"))


def walk(value: object, path: str = "$"):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def collect_links(payload: object):
    rows = []
    for path, node in walk(payload):
        for key in ("links", "_links"):
            links = node.get(key) if isinstance(node, dict) else None
            if not isinstance(links, dict):
                continue
            for relation, value in links.items():
                if isinstance(value, dict):
                    value = value.get("href")
                if isinstance(value, str) and value:
                    rows.append({"json_path": f"{path}.{key}.{relation}", "relation": relation, "url": urljoin(BASE, value)})
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_doi")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)
    doi = args.dataset_doi.removeprefix("doi:").removeprefix("https://doi.org/").lower()
    dataset_url = f"{BASE}/api/v2/datasets/{quote(f'doi:{doi}', safe='')}"
    _, dataset = fetch(dataset_url)
    version_href = dataset["_links"]["stash:version"]["href"]
    version_url = urljoin(BASE, version_href)
    status, version = fetch(version_url)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "dryad_version_payload.json").write_text(json.dumps(version, indent=2, sort_keys=True), encoding="utf-8")
    with (out / "dryad_version_links.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["json_path", "relation", "url"])
        writer.writeheader()
        writer.writerows(collect_links(version))
    report = {"dataset_doi": doi, "dataset_url": dataset_url, "version_url": version_url, "http_status": status}
    (out / "dryad_version_inspection_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
