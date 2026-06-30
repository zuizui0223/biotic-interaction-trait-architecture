"""Screen README/R documentation in a title-validated Dryad archive.

The script writes only a compact keyword index: file name, matched concept, and
short line fragments. It never writes observation rows. It is a documentation
screen for unit, timing, trait-function, and denominator metadata before any
four-path model is specified.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import defaultdict
from io import BytesIO
from pathlib import Path

from trait_architecture.dryad_archive_schema import _download_archive, _version_url
from trait_architecture.title_validated_dryad_manifest import probe_targets, read_targets


KEYWORDS = {
    "unit_or_linkage": ("plot", "plant", "individual", "flower", "id"),
    "timing": ("date", "early", "late", "season", "before", "after"),
    "attraction": ("flower size", "nectar", "anthocyan", "redness", "color", "spur"),
    "barrier": ("tannin", "defense", "defence", "florivory"),
    "pollination": ("pollinator", "visitor", "robber", "thief", "pollination"),
    "antagonism": ("florivory", "damage", "herbivor"),
    "fitness": ("fruit", "seed", "reproduction", "mature"),
}
MAX_MATCHES_PER_FILE_CONCEPT = 3
MAX_FRAGMENT_CHARS = 260


def _text(value: object) -> str:
    return str(value or "").strip()


def _pick_receipt(targets: list[dict[str, str]]):
    receipts, report = probe_targets(targets)
    for receipt in receipts:
        if receipt.manifest_status == "manifest_recovered" and _version_url(receipt):
            return receipt, report
    raise RuntimeError("no title-validated Dryad manifest with a version endpoint was recovered")


def _fragment(line: str) -> str:
    line = re.sub(r"\s+", " ", line).strip()
    return line[:MAX_FRAGMENT_CHARS]


def screen(targets_csv: str, out_dir: str) -> dict[str, object]:
    targets = read_targets(targets_csv)
    receipt, manifest_report = _pick_receipt(targets)
    archive_url = f"{_version_url(receipt)}/download"
    archive_bytes = _download_archive(archive_url, landing_page_url=receipt.landing_page_url)
    archive = zipfile.ZipFile(BytesIO(archive_bytes))
    matches: list[dict[str, str]] = []
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for member in sorted(archive.infolist(), key=lambda item: item.filename):
        if member.is_dir() or not member.filename.lower().endswith(".txt"):
            continue
        content = archive.read(member).decode("utf-8", errors="replace")
        for line_number, line in enumerate(content.splitlines(), start=1):
            lowered = line.lower()
            for concept, terms in KEYWORDS.items():
                key = (member.filename, concept)
                if counts[key] >= MAX_MATCHES_PER_FILE_CONCEPT:
                    continue
                if any(term in lowered for term in terms):
                    matches.append({
                        "file_name": member.filename,
                        "concept": concept,
                        "line_number": str(line_number),
                        "fragment": _fragment(line),
                    })
                    counts[key] += 1
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    payload = {
        "study_id": receipt.study_id,
        "study_doi": receipt.study_doi,
        "dataset_doi": receipt.dataset_doi,
        "archive_url": archive_url,
        "manifest": manifest_report,
        "matched_fragments": matches,
        "warning": "Documentation fragments guide manual semantic screening only. They are not raw observations, effect estimates, or a causal identification claim.",
    }
    (output / "dryad_documentation_keyword_screen.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    return {
        "study_id": receipt.study_id,
        "dataset_doi": receipt.dataset_doi,
        "text_file_count": sum(not member.is_dir() and member.filename.lower().endswith(".txt") for member in archive.infolist()),
        "matched_fragment_count": len(matches),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)
    print(json.dumps(screen(args.targets_csv, args.out_dir), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
