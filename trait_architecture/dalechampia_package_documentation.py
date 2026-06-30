"""Inspect name-whitelisted documentation inside the public *Dalechampia* archive.

The linked Dryad package contains raw observation tables. This module never emits
those rows. It reads only a small, explicit allow-list of documentation names
(e.g. ``README`` or ``stash``), records bounded text excerpts in workflow
artifacts, and leaves trait-role decisions to a separate primary-source review.
"""

from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Callable

from trait_architecture.dalechampia_linked_panel import _dataset_chain, _fetch_bytes, _fetch_json, _normalise_doi


DOCUMENTATION_BASENAMES = frozenset({
    "readme",
    "readme.txt",
    "readme.md",
    "metadata",
    "metadata.txt",
    "methods",
    "methods.txt",
    "documentation",
    "documentation.txt",
    "stash",
})
MAX_DOCUMENTATION_BYTES = 32_768
MAX_EXCERPT_CHARACTERS = 8_000


def _is_documentation_member(name: str) -> bool:
    return Path(name).name.lower() in DOCUMENTATION_BASENAMES


def _excerpt(content: bytes) -> tuple[str, bool]:
    """Return a bounded readable excerpt and whether source bytes were truncated."""

    truncated = len(content) > MAX_DOCUMENTATION_BYTES
    text = content[:MAX_DOCUMENTATION_BYTES].decode("utf-8-sig", errors="replace")
    text = text.replace("\x00", "").strip()
    if len(text) > MAX_EXCERPT_CHARACTERS:
        text = text[:MAX_EXCERPT_CHARACTERS].rstrip() + "\n[excerpt truncated]"
        truncated = True
    return text, truncated


def inspect_package_documentation(
    dataset_doi: str,
    *,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
    fetch_bytes: Callable[[str], bytes] = _fetch_bytes,
) -> dict[str, object]:
    """Return bounded documentation excerpts without retaining observation rows."""

    dataset_doi = _normalise_doi(dataset_doi)
    file_names, version_url, archive_url = _dataset_chain(dataset_doi, fetch_json)
    archive = zipfile.ZipFile(BytesIO(fetch_bytes(archive_url)))
    records: list[dict[str, object]] = []

    for member in sorted(archive.infolist(), key=lambda item: item.filename):
        if member.is_dir() or not _is_documentation_member(member.filename):
            continue
        excerpt, truncated = _excerpt(archive.read(member))
        records.append({
            "file_name": member.filename,
            "status": "excerpt_recovered" if excerpt else "empty_documentation_file",
            "excerpt": excerpt,
            "truncated": truncated,
            "notes": "Name-whitelisted documentation only; no observation-table rows are emitted.",
        })

    return {
        "dataset_doi": dataset_doi,
        "version_url": version_url,
        "archive_url": archive_url,
        "manifest_file_count": len(file_names),
        "documentation_allowlist": sorted(DOCUMENTATION_BASENAMES),
        "documentation_record_count": len(records),
        "records": records,
        "decision_boundary": "Documentation excerpts establish neither trait function nor an eligible four-path effect. They are limited to locating variable definitions and study context for a later manual screen.",
    }


def write_documentation_inspection(out_dir: str | Path, report: dict[str, object]) -> None:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "dalechampia_package_documentation_inspection.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
