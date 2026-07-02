"""Fixed-corpus triage and safe synthesis contracts for floral trait--animal responses.

This module deliberately separates the broader effect-size synthesis from the
previous narrow "direct floral defence" question.  It accepts four empirical
channels:

    A_flower -> pollinator response
    A_flower -> floral-antagonist response
    B_flower -> pollinator response
    B_flower -> floral-antagonist response

The fixed L1 corpus supplies candidate abstracts only.  Full-text adjudication
must establish trait role, study design, independence, outcome family, and a
recoverable effect size before a record can enter an effect-size analysis.

No publication count, abstract label, or model-assisted code is interpreted as
an effect size or a numerical parameter of the attraction--defence model.
"""

from __future__ import annotations

import csv
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist
from typing import Iterable, Mapping


ROUTE_FIELDS: Mapping[str, str] = {
    "A_to_pollinator": "candidate_A_to_P",
    "A_to_antagonist": "candidate_A_to_H",
    "B_to_antagonist": "candidate_B_to_H",
    "B_to_pollinator": "candidate_B_to_P",
}
ROUTE_ORDER = tuple(ROUTE_FIELDS)

ROUTE_INTERPRETATION = {
    "A_to_pollinator": "Positive values mean that higher attraction increases pollinator response; this is directionally consistent with b_A > 0.",
    "A_to_antagonist": "Positive values mean that higher attraction increases floral-antagonist response; this is directionally consistent with d_A > 0.",
    "B_to_antagonist": "Negative values mean that stronger floral barriers/deterrence reduce floral-antagonist response; this is directionally consistent with e_F > 0.",
    "B_to_pollinator": "Negative values mean that stronger floral barriers/deterrence reduce pollinator response; this is directionally consistent with c_D > 0.",
}

SOURCE_BUCKETS = ("empirical_nonreview", "other")

# These tags rank records for full-text screening only. They are intentionally
# broad and never determine inclusion by themselves.
CUE_PATTERNS = {
    "experimental": r"\b(?:manipulat(?:e|ed|ion)|experiment(?:al|s)?|treatment|treated|control(?:led)?|supplement(?:ed|ation)?|remov(?:e|ed|al)|artificial|transgenic|knockout|mutant|exclusion|cage|bagg(?:ed|ing)|paint(?:ed|ing)|clipp(?:ed|ing)|appl(?:y|ied|ication))\b",
    "choice": r"\b(?:choice|preference|prefer(?:red|ence)?|dual[- ]choice|two[- ]choice|foraging choice|avoid(?:ed|ance))\b",
    "association": r"\b(?:correlat(?:e|ed|ion)|association|associated|regression|relationship|relat(?:e|ed)|predict(?:ed|or|ion)|selection gradient|covar(?:y|iation)|linear model|mixed model|glm|glmm)\b",
    "effect_statistics": r"\b(?:mean|standard deviation|confidence interval|odds ratio|risk ratio|response ratio|effect size|correlation coefficient|pearson|spearman|fisher|p\s*[<=>]|t\s*=|f\s*=|z\s*=|chi[- ]?square|n\s*=)\b",
    "pollinator_outcome": r"\b(?:visit(?:ation|ed|s)?|forag(?:e|ing)|pollinat(?:or|ion)|handling time|residence time|flower constancy|nectar removal|pollen removal|pollen deposition|stigma|anther)\b",
    "antagonist_outcome": r"\b(?:florivor(?:y|e|ous)|herbivor(?:y|e|ous)|damage|damaged|predat(?:ion|or)|nectar robb(?:er|ing)|robbery|seed predation|attack|consumer|chew(?:ing|ed)|larva|caterpillar)\b",
}
COMPILED_CUES = {name: re.compile(pattern, flags=re.IGNORECASE) for name, pattern in CUE_PATTERNS.items()}

RECORD_REQUIRED = {
    "candidate_id", "doi", "publication_year", "work_type", "route_families", "source_queries",
    "shallow_screen_status", "crossref_abstract_available", "floral_context_signal",
    "empirical_language_signal", "review_language_signal", "candidate_A_to_P", "candidate_A_to_H",
    "candidate_B_to_H", "candidate_B_to_P",
}
PACKET_REQUIRED = {
    "candidate_id", "doi", "title", "publication_year", "work_type", "container_title", "publisher",
    "crossref_abstract_available", "crossref_abstract_text",
}

CANDIDATE_QUEUE_FIELDS = (
    "candidate_id", "doi", "title", "publication_year", "work_type", "container_title", "publisher",
    "source_queries", "route_families", "shallow_screen_status", "source_bucket", "route_memberships",
    "abstract_available", "empirical_language_signal", "review_language_signal", "cue_experimental",
    "cue_choice", "cue_association", "cue_effect_statistics", "cue_pollinator_outcome", "cue_antagonist_outcome",
    "screening_priority", "screening_rationale", "full_text_screen_status", "full_text_screen_note",
    "crossref_abstract_text", "candidate_warning",
)

EXTRACTION_FIELDS = (
    "candidate_id", "route", "study_id", "effect_id", "species", "study_year", "trait_name", "trait_role",
    "organ_match", "trait_contrast_or_predictor", "partner_response", "outcome_family", "study_design",
    "effect_family", "effect_estimate", "effect_variance", "sample_size_total", "independent_study_id",
    "is_primary_effect_for_study", "full_text_inclusion", "exclusion_reason", "source_locator", "extractor_id",
    "extraction_note", "direction_convention",
)

ALLOWED_TRAIT_ROLES = frozenset({"A_flower", "B_flower"})
ALLOWED_ORGAN_MATCH = frozenset({"flower_or_inflorescence", "nectar", "reproductive_structure"})
ALLOWED_PARTNER_RESPONSES = frozenset({"pollinator", "floral_antagonist"})
ALLOWED_OUTCOME_FAMILIES = frozenset({
    "visitation_or_foraging", "choice_or_preference", "pollen_transfer", "floral_damage_or_attack",
    "floral_antagonist_abundance", "reproductive_output", "other_predeclared",
})
ALLOWED_STUDY_DESIGNS = frozenset({"direct_experiment", "choice_assay", "observational_association"})
ALLOWED_EFFECT_FAMILIES = frozenset({"log_response_ratio", "hedges_g", "log_odds_ratio", "log_rate_ratio", "fisher_z"})


class FloralTraitResponseMetaError(ValueError):
    """Raised when candidate or effect-size tables violate the meta-analysis contract."""


def _text(value: object) -> str:
    return str(value or "").strip()


def _truth(value: object) -> bool:
    return _text(value).lower() in {"1", "true", "yes", "y"}


def read_rows(path: str | Path, required_fields: Iterable[str]) -> list[dict[str, str]]:
    location = Path(path)
    with location.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(required_fields).difference(reader.fieldnames or [])
        if missing:
            raise FloralTraitResponseMetaError(
                f"{location} missing required columns: {', '.join(sorted(missing))}"
            )
        return [{key: _text(value) for key, value in row.items()} for row in reader]


def _source_bucket(row: Mapping[str, str]) -> str:
    return "empirical_nonreview" if _truth(row.get("empirical_language_signal")) and not _truth(row.get("review_language_signal")) else "other"


def _route_memberships(row: Mapping[str, str]) -> list[str]:
    return [route for route, field in ROUTE_FIELDS.items() if _truth(row.get(field))]


def _cue_matches(abstract: str) -> dict[str, bool]:
    return {name: bool(pattern.search(abstract)) for name, pattern in COMPILED_CUES.items()}


def _screening_priority(cues: Mapping[str, bool], empirical_nonreview: bool) -> tuple[str, str]:
    """Return a reproducible full-text screen tier, never an inclusion decision."""
    response_cue = cues["pollinator_outcome"] or cues["antagonist_outcome"]
    if empirical_nonreview and cues["experimental"] and cues["effect_statistics"] and response_cue:
        return "tier_1_direct_effect_candidate", "empirical abstract with experimental, outcome, and statistic cues"
    if empirical_nonreview and cues["choice"] and cues["effect_statistics"] and response_cue:
        return "tier_1_choice_effect_candidate", "empirical abstract with choice, outcome, and statistic cues"
    if empirical_nonreview and cues["association"] and cues["effect_statistics"] and response_cue:
        return "tier_2_association_effect_candidate", "empirical abstract with association, outcome, and statistic cues"
    if empirical_nonreview:
        return "tier_3_empirical_full_text_screen", "empirical-language abstract; effect recoverability unknown until full text"
    return "tier_4_context_or_review", "context/review/uncertain abstract retained for audit traceability, not first-pass extraction"


def build_candidate_queue(
    evidence_records: Iterable[Mapping[str, str]], abstract_packet: Iterable[Mapping[str, str]],
) -> list[dict[str, str]]:
    """Build one fixed-corpus candidate queue across all four model channels.

    The queue contains every record with a retrieved abstract, flower-context
    signal, and at least one A/B x P/H candidate edge. It does not discover new
    records or decide that an effect size exists.
    """
    records, packet = list(evidence_records), list(abstract_packet)
    record_ids = [row["candidate_id"] for row in records]
    packet_ids = [row["candidate_id"] for row in packet]
    if len(record_ids) != len(set(record_ids)) or len(packet_ids) != len(set(packet_ids)):
        raise FloralTraitResponseMetaError("candidate_id must be unique in both fixed-corpus inputs")
    if set(record_ids) != set(packet_ids):
        raise FloralTraitResponseMetaError("evidence records and abstract packet must have identical candidate IDs")
    packet_by_id = {row["candidate_id"]: row for row in packet}

    queue: list[dict[str, str]] = []
    for record in records:
        if not (_truth(record.get("crossref_abstract_available")) and _truth(record.get("floral_context_signal"))):
            continue
        routes = _route_memberships(record)
        if not routes:
            continue
        source = packet_by_id[record["candidate_id"]]
        abstract = _text(source.get("crossref_abstract_text"))
        cues = _cue_matches(abstract)
        source_bucket = _source_bucket(record)
        priority, rationale = _screening_priority(cues, source_bucket == "empirical_nonreview")
        queue.append({
            "candidate_id": _text(record.get("candidate_id")), "doi": _text(record.get("doi")),
            "title": _text(source.get("title")), "publication_year": _text(source.get("publication_year") or record.get("publication_year")),
            "work_type": _text(source.get("work_type") or record.get("work_type")),
            "container_title": _text(source.get("container_title")), "publisher": _text(source.get("publisher")),
            "source_queries": _text(record.get("source_queries")), "route_families": _text(record.get("route_families")),
            "shallow_screen_status": _text(record.get("shallow_screen_status")), "source_bucket": source_bucket,
            "route_memberships": ";".join(routes), "abstract_available": "true",
            "empirical_language_signal": _text(record.get("empirical_language_signal")),
            "review_language_signal": _text(record.get("review_language_signal")),
            "cue_experimental": str(cues["experimental"]).lower(), "cue_choice": str(cues["choice"]).lower(),
            "cue_association": str(cues["association"]).lower(),
            "cue_effect_statistics": str(cues["effect_statistics"]).lower(),
            "cue_pollinator_outcome": str(cues["pollinator_outcome"]).lower(),
            "cue_antagonist_outcome": str(cues["antagonist_outcome"]).lower(),
            "screening_priority": priority, "screening_rationale": rationale,
            "full_text_screen_status": "unreviewed", "full_text_screen_note": "",
            "crossref_abstract_text": abstract,
            "candidate_warning": (
                "Fixed-corpus full-text screening candidate only. Abstract cues do not establish trait role, causal design, independent study identity, or effect-size recoverability."
            ),
        })
    return sorted(queue, key=lambda row: (row["screening_priority"], row["candidate_id"]))


def make_extraction_sheet(candidate_queue: Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    """Create one blank row for every candidate-route membership.

    Full-text screening can create additional rows when a study reports multiple
    independent effects. The initial rows are a traceable screening ledger, not
    the final effect-size table.
    """
    rows: list[dict[str, str]] = []
    for candidate in candidate_queue:
        for route in filter(None, _text(candidate.get("route_memberships")).split(";")):
            trait_role = "A_flower" if route.startswith("A_") else "B_flower"
            partner = "pollinator" if route.endswith("pollinator") else "floral_antagonist"
            rows.append({
                "candidate_id": _text(candidate.get("candidate_id")), "route": route,
                "study_id": "", "effect_id": "", "species": "", "study_year": _text(candidate.get("publication_year")),
                "trait_name": "", "trait_role": trait_role, "organ_match": "", "trait_contrast_or_predictor": "",
                "partner_response": partner, "outcome_family": "", "study_design": "", "effect_family": "",
                "effect_estimate": "", "effect_variance": "", "sample_size_total": "", "independent_study_id": "",
                "is_primary_effect_for_study": "", "full_text_inclusion": "pending_full_text", "exclusion_reason": "",
                "source_locator": "", "extractor_id": "", "extraction_note": "",
                "direction_convention": ROUTE_INTERPRETATION[route],
            })
    return rows


def validate_effect_rows(rows: Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    """Validate full-text extraction rows before any numerical synthesis.

    Included effects must be organ-matched, route-consistent, recoverable, and
    assigned to a design/effect family that may be pooled only with the same
    family. Observational Fisher-z effects may not be silently pooled with
    experimental log ratios or standardized mean differences.
    """
    seen_effect_ids: set[str] = set()
    normalized: list[dict[str, str]] = []
    for source in rows:
        row = {key: _text(value) for key, value in source.items()}
        inclusion = row.get("full_text_inclusion", "")
        if inclusion not in {"included", "excluded", "pending_full_text"}:
            raise FloralTraitResponseMetaError("full_text_inclusion must be included, excluded, or pending_full_text")
        if inclusion != "included":
            normalized.append(row)
            continue
        route = row.get("route", "")
        if route not in ROUTE_FIELDS:
            raise FloralTraitResponseMetaError(f"included row has invalid route: {route}")
        trait_role = row.get("trait_role", "")
        partner = row.get("partner_response", "")
        if trait_role not in ALLOWED_TRAIT_ROLES or partner not in ALLOWED_PARTNER_RESPONSES:
            raise FloralTraitResponseMetaError("included row requires an allowed trait_role and partner_response")
        expected_trait = "A_flower" if route.startswith("A_") else "B_flower"
        expected_partner = "pollinator" if route.endswith("pollinator") else "floral_antagonist"
        if trait_role != expected_trait or partner != expected_partner:
            raise FloralTraitResponseMetaError("included route, trait_role, and partner_response must agree")
        if row.get("organ_match") not in ALLOWED_ORGAN_MATCH:
            raise FloralTraitResponseMetaError("included row requires flower/nectar/reproductive organ match")
        if row.get("outcome_family") not in ALLOWED_OUTCOME_FAMILIES:
            raise FloralTraitResponseMetaError("included row requires an allowed outcome_family")
        design = row.get("study_design")
        family = row.get("effect_family")
        if design not in ALLOWED_STUDY_DESIGNS or family not in ALLOWED_EFFECT_FAMILIES:
            raise FloralTraitResponseMetaError("included row requires allowed study_design and effect_family")
        if design == "observational_association" and family != "fisher_z":
            raise FloralTraitResponseMetaError("observational associations must use fisher_z in this v1 contract")
        if design in {"direct_experiment", "choice_assay"} and family == "fisher_z":
            raise FloralTraitResponseMetaError("experimental and choice effects may not use fisher_z in this v1 contract")
        try:
            effect, variance = float(row.get("effect_estimate", "")), float(row.get("effect_variance", ""))
        except ValueError as error:
            raise FloralTraitResponseMetaError("included row requires numeric effect_estimate and effect_variance") from error
        if not math.isfinite(effect) or not math.isfinite(variance) or variance <= 0:
            raise FloralTraitResponseMetaError("included effect_estimate must be finite and effect_variance positive")
        effect_id = row.get("effect_id", "")
        study_id = row.get("independent_study_id", "")
        if not effect_id or effect_id in seen_effect_ids or not study_id:
            raise FloralTraitResponseMetaError("included rows require unique effect_id and independent_study_id")
        seen_effect_ids.add(effect_id)
        normalized.append(row)
    return normalized


@dataclass(frozen=True)
class RandomEffectsSummary:
    route: str
    study_design: str
    outcome_family: str
    effect_family: str
    independent_studies: int
    estimate: float
    standard_error: float
    ci_low: float
    ci_high: float
    tau_squared: float
    status: str


def _dersimonian_laird(effects: list[tuple[float, float]]) -> tuple[float, float, float]:
    weights = [1 / variance for _, variance in effects]
    fixed = sum(weight * effect for weight, (effect, _) in zip(weights, effects)) / sum(weights)
    q = sum(weight * (effect - fixed) ** 2 for weight, (effect, _) in zip(weights, effects))
    df = len(effects) - 1
    c = sum(weights) - sum(weight ** 2 for weight in weights) / sum(weights)
    tau_squared = max(0.0, (q - df) / c) if c > 0 else 0.0
    random_weights = [1 / (variance + tau_squared) for _, variance in effects]
    estimate = sum(weight * effect for weight, (effect, _) in zip(random_weights, effects)) / sum(random_weights)
    standard_error = math.sqrt(1 / sum(random_weights))
    return estimate, standard_error, tau_squared


def summarize_ready_groups(rows: Iterable[Mapping[str, str]], minimum_independent_studies: int = 5) -> list[RandomEffectsSummary]:
    """Summarize eligible groups without mixing metrics, outcomes, or designs.

    The function requires one primary effect per independent study within each
    group. This avoids pseudo-replication until a future multilevel dependency
    model is explicitly declared.
    """
    if minimum_independent_studies < 2:
        raise FloralTraitResponseMetaError("minimum_independent_studies must be at least two")
    included = [row for row in validate_effect_rows(rows) if row.get("full_text_inclusion") == "included"]
    groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in included:
        groups[(row["route"], row["study_design"], row["outcome_family"], row["effect_family"])].append(row)
    summaries: list[RandomEffectsSummary] = []
    normal = NormalDist()
    for (route, design, outcome, family), group in sorted(groups.items()):
        primary = [row for row in group if row.get("is_primary_effect_for_study", "").lower() in {"true", "yes", "1"}]
        study_ids = [row["independent_study_id"] for row in primary]
        if len(study_ids) != len(set(study_ids)):
            raise FloralTraitResponseMetaError(
                f"{route}/{design}/{outcome}/{family} has more than one primary effect for an independent study"
            )
        k = len(primary)
        if k < minimum_independent_studies:
            summaries.append(RandomEffectsSummary(route, design, outcome, family, k, math.nan, math.nan, math.nan, math.nan, math.nan, "insufficient_independent_studies"))
            continue
        effect_pairs = [(float(row["effect_estimate"]), float(row["effect_variance"])) for row in primary]
        estimate, se, tau2 = _dersimonian_laird(effect_pairs)
        critical = normal.inv_cdf(0.975)
        summaries.append(RandomEffectsSummary(route, design, outcome, family, k, estimate, se, estimate - critical * se, estimate + critical * se, tau2, "ready_random_effects"))
    return summaries


def _write_csv(path: Path, fields: Iterable[str], rows: Iterable[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in writer.fieldnames})


def write_candidate_packet(out_dir: str | Path, queue: list[dict[str, str]], extraction: list[dict[str, str]]) -> None:
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    _write_csv(destination / "floral_trait_animal_response_candidate_queue.csv", CANDIDATE_QUEUE_FIELDS, queue)
    _write_csv(destination / "floral_trait_animal_response_effect_extraction.csv", EXTRACTION_FIELDS, extraction)
    _write_csv(
        destination / "floral_trait_animal_response_capacity.csv",
        ("route", "screening_priority", "candidate_records", "interpretation_boundary"),
        [
            {
                "route": route,
                "screening_priority": priority,
                "candidate_records": str(sum(route in row["route_memberships"].split(";") and row["screening_priority"] == priority for row in queue)),
                "interpretation_boundary": "Candidate abstract count for fixed-corpus full-text screening; not an included-study count or effect-size count.",
            }
            for route in ROUTE_ORDER
            for priority in (
                "tier_1_direct_effect_candidate", "tier_1_choice_effect_candidate", "tier_2_association_effect_candidate",
                "tier_3_empirical_full_text_screen", "tier_4_context_or_review",
            )
        ],
    )
    (destination / "README.md").write_text(
        "# Floral trait--animal response meta-analysis packet\n\n"
        "This packet expands full-text screening across A/B x pollinator/floral-antagonist channels while preserving separate effect-size families and study designs. "
        "It is not a discovery search and does not make any numerical inference from abstracts.\n",
        encoding="utf-8",
    )
