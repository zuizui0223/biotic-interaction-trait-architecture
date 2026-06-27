"""Deterministic helpers for the Megachile host-evidence pipeline.

The module manages search queries, metadata deduplication, evidence validation,
and construction of a plant universe from reviewed records. It never infers a
host interaction from an LLM answer or a bibliographic search result.
"""

from __future__ import annotations

from collections import defaultdict
from hashlib import sha1
import re
import unicodedata
from typing import Iterable, Mapping

DIRECT_MATERIAL_TYPES = frozenset(
    {
        "leaf_cutting_direct",
        "petal_cutting_direct",
        "nest_lining_direct",
        "resin_collection_direct",
    }
)
ALLOWED_INTERACTION_TYPES = DIRECT_MATERIAL_TYPES | frozenset(
    {
        "nest_material_unspecified",
        "floral_visit_only",
        "nest_near_plant_only",
        "co_occurrence_only",
        "unknown",
    }
)
ALLOWED_EVIDENCE_GRADES = frozenset({"A", "B", "C", "D", "E"})
PRIMARY_TAXON_STATUSES = frozenset({"accepted", "synonym_resolved"})


def _text(value: object | None) -> str:
    return "" if value is None else str(value).strip()


def normalise_title(value: object | None) -> str:
    """Return a conservative key for title-level duplicate detection."""
    text = unicodedata.normalize("NFKC", _text(value)).casefold()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def canonical_doi(value: object | None) -> str:
    """Normalise DOI-shaped strings without attempting DOI validation."""
    doi = _text(value).casefold()
    doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:)", "", doi)
    return doi.rstrip(" .;,)")


def stable_id(prefix: str, *parts: object) -> str:
    payload = "|".join(_text(part) for part in parts)
    return f"{prefix}_{sha1(payload.encode('utf-8')).hexdigest()[:12]}"


def build_query_rows(species_rows: Iterable[Mapping[str, object]]) -> list[dict[str, str]]:
    """Build deliberately small bilingual search queries per accepted bee taxon.

    Input rows need ``bee_name_accepted``. ``bee_name_japanese`` is optional.
    Generic genus-only terms are intentionally omitted here: they should be
    searched separately and entered with an explicit taxonomic uncertainty.
    """
    english_terms = (
        ("nest_material", "nest material"),
        ("leaf_cutting", "leaf cutting"),
        ("cut_leaves", '"cut leaves"'),
        ("nest_lining", "nest lining"),
        ("petal_cutting", "petal cutting"),
        ("resin", "resin"),
    )
    japanese_terms = (
        ("nest_material_ja", "巣材"),
        ("leaf_piece_ja", "葉片"),
        ("leaf_cutting_ja", "葉を切る"),
        ("nest_lining_ja", "巣内壁"),
        ("resin_ja", "樹脂"),
    )
    output: list[dict[str, str]] = []
    seen_taxa: set[str] = set()
    for row in species_rows:
        bee = _text(row.get("bee_name_accepted"))
        if not bee:
            raise ValueError("each species row needs bee_name_accepted")
        if bee in seen_taxa:
            raise ValueError(f"duplicate bee_name_accepted: {bee}")
        seen_taxa.add(bee)
        japanese_name = _text(row.get("bee_name_japanese"))
        for family, term in english_terms:
            query = f'"{bee}" AND ({term})'
            output.append(
                {
                    "query_id": stable_id("q", bee, "en", family),
                    "bee_name_accepted": bee,
                    "language": "en",
                    "query_family": family,
                    "query_string": query,
                    "purpose": "candidate nesting-material evidence",
                }
            )
        # Japanese phrase searches can use a Japanese common name when supplied;
        # Latin name is retained otherwise to avoid inventing common names.
        japanese_subject = japanese_name or bee
        for family, term in japanese_terms:
            query = f'"{japanese_subject}" AND "{term}"'
            output.append(
                {
                    "query_id": stable_id("q", bee, "ja", family),
                    "bee_name_accepted": bee,
                    "language": "ja",
                    "query_family": family,
                    "query_string": query,
                    "purpose": "candidate nesting-material evidence",
                }
            )
    return output


def source_fingerprint(row: Mapping[str, object]) -> str:
    """Return one readable, conservative metadata key for reporting purposes."""
    doi = canonical_doi(row.get("doi"))
    if doi:
        return f"doi:{doi}"
    title = normalise_title(row.get("title"))
    year = _text(row.get("publication_year"))
    first_author = _text(row.get("first_author"))
    if not title:
        return stable_id("source", row.get("provider"), row.get("provider_record_id"), row.get("source_url"))
    return f"title:{title}|{year}|{normalise_title(first_author)}"


def _duplicate_keys(row: Mapping[str, object]) -> tuple[str, ...]:
    """Return exact keys that can connect duplicate metadata records.

    DOI and exact title/year/first-author keys are both retained. This lets a
    rich record with a DOI join a sparse record that has only matching title
    metadata, without relying on fuzzy title matching.
    """
    keys: list[str] = []
    doi = canonical_doi(row.get("doi"))
    if doi:
        keys.append(f"doi:{doi}")
    title = normalise_title(row.get("title"))
    if title:
        year = _text(row.get("publication_year"))
        author = normalise_title(row.get("first_author"))
        keys.append(f"title:{title}|{year}|{author}")
    if not keys:
        keys.append(source_fingerprint(row))
    return tuple(keys)


def deduplicate_metadata(rows: Iterable[Mapping[str, object]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Keep one richest record per connected set of exact metadata keys.

    DOI and title keys are connected by records that contain both, so a record
    with a DOI can be deduplicated against a matching record lacking one. No
    fuzzy matching is used; near-duplicates remain reviewable.
    """
    clean_rows = [{str(key): _text(value) for key, value in row.items()} for row in rows]
    parent = list(range(len(clean_rows)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    key_owner: dict[str, int] = {}
    for index, row in enumerate(clean_rows):
        for key in _duplicate_keys(row):
            if key in key_owner:
                union(index, key_owner[key])
            else:
                key_owner[key] = index

    groups: dict[int, list[int]] = defaultdict(list)
    for index in range(len(clean_rows)):
        groups[find(index)].append(index)

    retained: list[dict[str, str]] = []
    discarded: list[dict[str, str]] = []
    for indices in sorted(groups.values(), key=lambda values: min(values)):
        def richness(index: int) -> tuple[int, int, int, str]:
            item = clean_rows[index]
            fields = ("doi", "abstract", "source_url", "fulltext_url", "title", "first_author")
            return (
                sum(bool(item.get(field)) for field in fields),
                len(item.get("abstract", "")),
                len(item.get("title", "")),
                item.get("provider_record_id", ""),
            )

        chosen_index = max(indices, key=richness)
        chosen = clean_rows[chosen_index].copy()
        keys = sorted({key for index in indices for key in _duplicate_keys(clean_rows[index])})
        fingerprint = next((key for key in keys if key.startswith("doi:")), keys[0])
        chosen.setdefault("source_id", stable_id("src", fingerprint))
        chosen["dedupe_fingerprint"] = fingerprint
        retained.append(chosen)
        for index in indices:
            if index == chosen_index:
                continue
            item = clean_rows[index]
            discarded.append(
                {
                    "discarded_provider": item.get("provider", ""),
                    "discarded_provider_record_id": item.get("provider_record_id", ""),
                    "kept_source_id": chosen["source_id"],
                    "dedupe_fingerprint": fingerprint,
                    "reason": "same DOI or exact normalized title/year/first-author key",
                }
            )
    return retained, discarded


def validate_host_evidence_record(row: Mapping[str, object]) -> tuple[list[str], list[str]]:
    """Return fatal errors and warnings for one reviewed host-evidence row."""
    errors: list[str] = []
    warnings: list[str] = []
    interaction = _text(row.get("interaction_type"))
    grade = _text(row.get("evidence_grade")).upper()
    country = _text(row.get("country"))
    include = _text(row.get("include_in_primary_host_universe")).upper() == "TRUE"
    status = _text(row.get("taxon_reconciliation_status"))

    required = (
        "record_id",
        "bee_name_reported",
        "plant_name_reported",
        "interaction_type",
        "evidence_grade",
        "source_type",
        "source_id",
        "source_locator",
    )
    for field in required:
        if not _text(row.get(field)):
            errors.append(f"missing required field: {field}")
    if interaction and interaction not in ALLOWED_INTERACTION_TYPES:
        errors.append(f"unknown interaction_type: {interaction}")
    if grade and grade not in ALLOWED_EVIDENCE_GRADES:
        errors.append(f"unknown evidence_grade: {grade}")

    direct = interaction in DIRECT_MATERIAL_TYPES
    primary_ready = (
        direct
        and grade in {"A", "B"}
        and country == "Japan"
        and bool(_text(row.get("bee_name_accepted")))
        and bool(_text(row.get("plant_name_accepted")))
        and status in PRIMARY_TAXON_STATUSES
    )
    if include and not primary_ready:
        errors.append("record marked primary but does not meet direct/Japan/A-or-B/taxonomy criteria")
    if not include and primary_ready:
        warnings.append("record is eligible for primary universe but currently not marked TRUE")
    if interaction == "floral_visit_only":
        warnings.append("floral visit is not nesting-material evidence")
    if interaction in {"co_occurrence_only", "nest_near_plant_only"}:
        warnings.append("association record is not material-use evidence")
    if grade == "C":
        warnings.append("secondary citation requires primary-source audit before primary use")
    if status in {"unresolved", "not_checked", "genus_only"}:
        warnings.append("taxonomy is not ready for species-level trait analysis")
    return errors, warnings


def primary_host_universe(rows: Iterable[Mapping[str, object]]) -> list[dict[str, str]]:
    """Aggregate reviewed, explicitly primary rows into one row per plant taxon."""
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        if _text(row.get("include_in_primary_host_universe")).upper() != "TRUE":
            continue
        errors, _ = validate_host_evidence_record(row)
        if errors:
            continue
        grouped[_text(row.get("plant_name_accepted"))].append(row)

    grade_rank = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
    output: list[dict[str, str]] = []
    for plant, group in sorted(grouped.items()):
        bee_species = sorted({_text(row.get("bee_name_accepted")) for row in group})
        source_ids = sorted({_text(row.get("source_id")) for row in group})
        best_grade = min((_text(row.get("evidence_grade")).upper() for row in group), key=lambda grade: grade_rank[grade])
        output.append(
            {
                "plant_name_accepted": plant,
                "number_of_direct_records": str(len(group)),
                "number_of_bee_species": str(len(bee_species)),
                "bee_species": ";".join(bee_species),
                "supporting_source_count": str(len(source_ids)),
                "supporting_source_ids": ";".join(source_ids),
                "evidence_grade_best": best_grade,
                "Japan_record_count": str(sum(_text(row.get("country")) == "Japan" for row in group)),
                "trait_coverage_status": "not_yet_audited",
            }
        )
    return output
