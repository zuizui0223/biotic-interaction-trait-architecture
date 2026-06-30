"""Audit declared Figshare image ZIP manifests without reading image pixels.

The audit resolves exact archive names from an article-declared Figshare
accession. It emits aggregate member counts, extensions, and predeclared morph
and timestamp-token coverage only. Its default route reads only ZIP central-
directory bytes with HTTP Range requests, not the image archive payload.
"""

from __future__ import annotations

import json
import re
import struct
import zipfile
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen

from trait_architecture.declared_figshare_receipts import FIGSHARE_API
from trait_architecture.public_repository_resolver import _as_url, _fetch_json, _text


MORPH_TOKENS = ("black", "red", "white")
IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".tif", ".tiff"})
TIMESTAMP_PATTERN = re.compile(r"(?:19|20)\d{2}[-_]?\d{2}[-_]?\d{2}|\d{2}[-_:]\d{2}[-_:]\d{2}")
USER_AGENT = "biotic-interaction-trait-architecture declared-figshare-image-manifest/0.2"
TAIL_BYTES = 131_072
EOCD_SIGNATURE = b"PK\x05\x06"
CENTRAL_SIGNATURE = b"PK\x01\x02"


def _declared_file(payload: dict[str, Any], file_name: str) -> dict[str, Any]:
    matches = [item for item in payload.get("files", []) if isinstance(item, dict) and _text(item.get("name")) == file_name]
    if len(matches) != 1:
        raise ValueError("declared Figshare archive name is absent or ambiguous")
    return matches[0]


def _manifest_size(item: dict[str, Any]) -> int:
    """Read the public Figshare manifest's exact file size without a HEAD probe."""

    try:
        value = int(item.get("size"))
    except (TypeError, ValueError) as error:
        raise ValueError("declared Figshare archive manifest has no positive size") from error
    if value <= 0:
        raise ValueError("declared Figshare archive manifest size must be positive")
    return value


def _fetch_http_range(url: str, start: int, end: int, *, timeout: int = 45) -> bytes:
    request = Request(
        url,
        headers={"Range": f"bytes={start}-{end}", "User-Agent": USER_AGENT},
    )
    with urlopen(request, timeout=timeout) as response:  # nosec B310: exact public manifest URL
        status = int(getattr(response, "status", response.getcode()))
        if status != 206:
            raise ValueError("archive host did not honor bounded Range request")
        return response.read()


def _central_directory_names_from_bytes(data: bytes, *, archive_length: int | None = None) -> list[str]:
    """Extract filenames from a complete ZIP or a central-directory byte segment."""

    eocd_index = data.rfind(EOCD_SIGNATURE)
    if eocd_index >= 0:
        if eocd_index + 22 > len(data):
            raise ValueError("truncated ZIP end-of-central-directory record")
        directory_size = struct.unpack_from("<I", data, eocd_index + 12)[0]
        directory_offset = struct.unpack_from("<I", data, eocd_index + 16)[0]
        if archive_length is None:
            archive_length = len(data)
        tail_start = archive_length - len(data)
        relative_offset = directory_offset - tail_start
        if 0 <= relative_offset and relative_offset + directory_size <= len(data):
            data = data[relative_offset:relative_offset + directory_size]
        elif directory_offset == 0 and directory_size <= len(data):
            data = data[:directory_size]
        else:
            raise ValueError("central directory is outside supplied ZIP bytes")

    names: list[str] = []
    cursor = 0
    while cursor + 46 <= len(data):
        if data[cursor:cursor + 4] != CENTRAL_SIGNATURE:
            raise ValueError("invalid ZIP central-directory signature")
        file_name_length, extra_length, comment_length = struct.unpack_from("<HHH", data, cursor + 28)
        start = cursor + 46
        stop = start + file_name_length
        if stop > len(data):
            raise ValueError("truncated ZIP central-directory filename")
        names.append(data[start:stop].decode("utf-8", errors="replace"))
        cursor = stop + extra_length + comment_length
    return names


def _range_manifest_names(url: str, archive_length: int) -> list[str]:
    """Read only central-directory bytes from a public ZIP with Range requests."""

    tail_start = max(0, archive_length - TAIL_BYTES)
    tail = _fetch_http_range(url, tail_start, archive_length - 1)
    eocd_index = tail.rfind(EOCD_SIGNATURE)
    if eocd_index < 0:
        raise ValueError("ZIP end-of-central-directory not found in bounded tail")
    if eocd_index + 22 > len(tail):
        raise ValueError("truncated ZIP end-of-central-directory record")
    directory_size = struct.unpack_from("<I", tail, eocd_index + 12)[0]
    directory_offset = struct.unpack_from("<I", tail, eocd_index + 16)[0]
    if directory_offset >= tail_start and directory_offset + directory_size <= archive_length:
        segment = tail[directory_offset - tail_start:directory_offset - tail_start + directory_size]
    else:
        segment = _fetch_http_range(url, directory_offset, directory_offset + directory_size - 1)
    return _central_directory_names_from_bytes(segment)


def _member_summary_from_names(names: list[str]) -> dict[str, object]:
    members = [name for name in names if not name.endswith("/")]
    extensions: Counter[str] = Counter()
    morph_hits: Counter[str] = Counter()
    timestamp_name_count = 0
    image_count = 0
    for name in members:
        basename = Path(name).name.lower()
        suffix = Path(basename).suffix.lower()
        extensions[suffix or "[no_extension]"] += 1
        if suffix in IMAGE_EXTENSIONS:
            image_count += 1
        for morph in MORPH_TOKENS:
            if morph in basename:
                morph_hits[morph] += 1
        if TIMESTAMP_PATTERN.search(basename):
            timestamp_name_count += 1
    return {
        "member_file_count": len(members),
        "image_file_count": image_count,
        "counts_by_extension": dict(sorted(extensions.items())),
        "filename_morph_token_counts": {morph: morph_hits[morph] for morph in MORPH_TOKENS},
        "filename_timestamp_token_count": timestamp_name_count,
    }


def _full_zip_names(fetch_bytes: Callable[[str], bytes], url: str) -> list[str]:
    """Test-only fallback for synthetic archives; production uses range manifests."""

    archive = zipfile.ZipFile(BytesIO(fetch_bytes(url)))
    return archive.namelist()


def audit_declared_figshare_image_manifests(
    *,
    figshare_article_id: str,
    archive_names: list[str],
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
    fetch_bytes: Callable[[str], bytes] | None = None,
) -> dict[str, object]:
    """Return aggregate ZIP manifest facts for exact declared pollinator archives.

    If the source refuses bounded Range requests, emit an explicit unavailable
    status rather than downloading the archive payload or failing the source
    audit. That outcome leaves image annotation unsupported, which is a valid
    evidence result.
    """

    accession = _text(figshare_article_id)
    request_url = FIGSHARE_API + accession
    status, payload = fetch_json(request_url)
    if status >= 400:
        raise RuntimeError(f"HTTP {status}")
    if not isinstance(payload, dict) or _text(payload.get("id")) != accession:
        raise ValueError("Figshare response did not match declared article accession")

    archives = []
    for name in archive_names:
        item = _declared_file(payload, name)
        url = _as_url(item.get("download_url"))
        if not url:
            raise ValueError("declared Figshare archive has no public download URL")
        try:
            names = (
                _full_zip_names(fetch_bytes, url)
                if fetch_bytes is not None
                else _range_manifest_names(url, _manifest_size(item))
            )
        except (OSError, ValueError) as error:
            archives.append({
                "archive_name": name,
                "manifest_status": "range_manifest_unavailable",
                "reason": str(error),
            })
            continue
        archives.append({
            "archive_name": name,
            "manifest_status": "manifest_recovered",
            **_member_summary_from_names(names),
        })
    return {
        "figshare_article_id": accession,
        "figshare_dataset_doi": _text(payload.get("doi")),
        "archives": archives,
        "decision_boundary": (
            "This audit emits aggregate ZIP-manifest properties only. It does not emit image paths or pixels, "
            "map frames to floral morphs, establish camera exposure, or count pollinator visits."
        ),
    }


def write_declared_figshare_image_manifest_audit(out_dir: str | Path, report: dict[str, object]) -> None:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "declared_figshare_image_manifest_audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
