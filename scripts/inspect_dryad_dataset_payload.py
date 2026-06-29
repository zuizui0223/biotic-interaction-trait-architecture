"""Save a Dryad dataset endpoint payload and every embedded link for inspection.

This is a source-structure diagnostic. It does not download data files.

Usage:
    python scripts/inspect_dryad_dataset_payload.py 10.5061/dryad.example artifacts/dryad_inspection
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


USER_AGENT = "biotic-interaction-trait-architecture dryad-payload-inspector/0.1"


def _text(value: object) -> str:
    return str(value or "").strip()


def _walk(payload: object, path: str = "$"):
    if isinstance(payload, dict):
        yield path, payload
        for key, value in payload.items():
            yield from _walk(value, f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            yield from _walk(value, f"{path}[{index}]")


def _url(value: object) -> str:
    value = _text(value)
    return value if value.startswith(("https://", "http://")) else ""


def inspect(doi: str, out_dir: str | Path, timeout: int = 20) -> dict[str, object]:
    doi = _text(doi).removeprefix("https://doi.org/").removeprefix("doi:").lower()
    endpoint = f"https://datadryad.org/api/v2/datasets/{quote(f'doi:{doi}', safe='')}"
    request = Request(endpoint, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed public endpoint
        status = int(getattr(response, "status", response.getcode()))
        payload = json.loads(response.read().decode("utf-8"))

    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "dryad_dataset_payload.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    links: list[dict[str, str]] = []
    for path, node in _walk(payload):
        for key in ("links", "_links"):
            candidates = node.get(key) if isinstance(node, dict) else None
            if not isinstance(candidates, dict):
                continue
            for relation, value in candidates.items():
                if isinstance(value, dict):
                    value = value.get("href")
                url = _url(value)
                if url:
                    links.append({"json_path": f"{path}.{key}.{relation}", "relation": relation, "url": url})
    with (output / "dryad_dataset_links.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["json_path", "relation", "url"])
        writer.writeheader()
        writer.writerows(links)
    report = {"doi": doi, "endpoint": endpoint, "http_status": status, "link_count": len(links)}
    (output / "dryad_dataset_inspection_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_doi")
    parser.add_argument("out_dir")
    parser.add_argument("--timeout-seconds", type=int, default=20)
    args = parser.parse_args(argv)
    print(json.dumps(inspect(args.dataset_doi, args.out_dir, args.timeout_seconds), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
