"""Produce a shallow, broad abstract-level evidence map for the A-B-P-H model.

This module intentionally codes *co-mention candidates*, not causal effects.  It
is designed to answer where the fixed literature corpus contains organ-matched
abstract-level attention to each model edge, and where it does not.

Signs and model parameter use are supplied only by the separate source-adjudicated
route registry.  No abstract keyword pattern is converted into an effect size or
parameter magnitude.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


FLORAL_CONTEXT_TERMS = (
    "floral", "flower", "flowers", "corolla", "petal", "petals", "nectar", "inflorescence",
    "inflorescences", "bract", "bracts", "capitulum", "capitula", "anther", "stigma",
)
A_TERMS = (
    "colour", "color", "display", "floral size", "flower size", "scent", "fragrance", "reward",
    "nectar reward", "nectar volume", "nectar production", "nectar secretion", "sugar concentration",
    "orientation", "resupination", "corolla", "petal", "inflorescence", "floral signal",
    "flower shape", "floral morphology",
)
B_CORE_TERMS = (
    "defence", "defense", "alkaloid", "toxin", "toxic", "chemical deterrent", "deterrence",
    "repellent", "secondary metabolite", "phenolic", "tannin", "trichome", "spine", "spines",
    "sticky", "nectar alkaloid", "barrier",
)
B_CONTEXTUAL_TERMS = ("volatile", "volatiles")
P_TERMS = (
    "pollination", "pollinator", "pollinators", "visitation", "visitor", "visitors", "pollen transfer",
    "pollen deposition", "pollen receipt", "pollen removal", "pollination success", "outcross",
)
H_TERMS = (
    "florivory", "florivore", "florivores", "floral herbivory", "flower herbivory", "floral damage",
    "flower damage", "seed predation", "flower predator", "nectar robber", "nectar robbery", "pollen thief",
    "pollen theft",
)
W_TERMS = (
    "fruit set", "seed set", "reproductive success", "fitness", "seed production", "fruit production",
    "fecundity",
)
EMPIRICAL_TERMS = (
    "experiment", "experimental", "manipulat", "treatment", "we measured", "we examined", "we tested",
    "we investigated", "field study", "field experiment", "observed", "observation", "survey",
)
REVIEW_TERMS = ("review", "meta-analysis", "meta analysis", "systematic review", "synthesis")
SHARED_COST_TERMS = (
    "trade-off", "tradeoff", "allocation", "resource budget", "shared cost", "constraint", "cost of",
)

RECORD_FIELDS = (
    "candidate_id", "doi", "publication_year", "work_type", "route_families", "source_queries",
    "shallow_screen_status", "abstract_retrieval_state", "crossref_lookup_status",
    "crossref_abstract_available", "abstract_code_status", "floral_context_signal",
    "empirical_language_signal", "review_language_signal", "A_signal", "B_signal", "P_signal", "H_signal",
    "W_signal", "shared_cost_language_signal", "candidate_A_to_P", "candidate_A_to_H",
    "candidate_B_to_H", "candidate_B_to_P", "candidate_joint_channels", "coding_warning",
)
EDGE_SUMMARY_FIELDS = (
    "model_edge", "model_component", "fixed_l1_records", "abstract_retrieval_success_records",
    "floral_context_abstract_records", "broad_edge_candidate_records", "nonreview_edge_candidate_records",
    "empirical_language_edge_candidate_records", "priority_edge_candidate_records",
    "biological_context_edge_candidate_records", "coverage_status", "interpretation_boundary",
)

EDGE_DEFINITIONS = {
    "A_to_pollination": ("b_A", "candidate_A_to_P"),
    "A_to_antagonism": ("d_A", "candidate_A_to_H"),
    "B_to_antagonism": ("e_F", "candidate_B_to_H"),
    "B_to_pollination": ("c_D", "candidate_B_to_P"),
    "joint_channels": ("joint_A_B_P_H_context", "candidate_joint_channels"),
}


class BroadAbstractCodingError(ValueError):
    """Raised when the broad abstract packet lacks its frozen-corpus contract."""


def text(value: object) -> str:
    return str(value or "").strip()


def is_true(value: object) -> bool:
    return text(value).lower() in {"true", "1", "yes", "y"}


def has_any(value: str, terms: Iterable[str]) -> bool:
    return any(term in value for term in terms)


def read_packet(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = [{key: text(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    required = {"candidate_id", "crossref_abstract_text", "crossref_lookup_status", "shallow_screen_status"}
    if rows and not required.issubset(rows[0]):
        raise BroadAbstractCodingError("broad abstract packet lacks required columns")
    return rows


def classify_row(row: dict[str, str]) -> dict[str, str]:
    abstract = text(row.get("crossref_abstract_text")).lower()
    available = is_true(row.get("crossref_abstract_available")) and bool(abstract)
    floral = has_any(abstract, FLORAL_CONTEXT_TERMS) if available else False
    h_signal = has_any(abstract, H_TERMS) if available else False
    a_signal = floral and has_any(abstract, A_TERMS)
    b_core = floral and has_any(abstract, B_CORE_TERMS)
    b_volatile_context = floral and has_any(abstract, B_CONTEXTUAL_TERMS) and h_signal
    b_signal = b_core or b_volatile_context
    p_signal = has_any(abstract, P_TERMS) if available else False
    w_signal = has_any(abstract, W_TERMS) if available else False
    empirical = has_any(abstract, EMPIRICAL_TERMS) if available else False
    review = has_any(abstract, REVIEW_TERMS) if available else False
    shared_cost = (a_signal and b_signal and has_any(abstract, SHARED_COST_TERMS)) if available else False
    return {
        "candidate_id": text(row.get("candidate_id")),
        "doi": text(row.get("doi")),
        "publication_year": text(row.get("publication_year")),
        "work_type": text(row.get("work_type")),
        "route_families": text(row.get("route_families")),
        "source_queries": text(row.get("source_queries")),
        "shallow_screen_status": text(row.get("shallow_screen_status")),
        "abstract_retrieval_state": text(row.get("abstract_retrieval_state")),
        "crossref_lookup_status": text(row.get("crossref_lookup_status")),
        "crossref_abstract_available": str(available).lower(),
        "abstract_code_status": "coded_crossref_abstract" if available else "abstract_unavailable_or_lookup_failed",
        "floral_context_signal": str(floral).lower(),
        "empirical_language_signal": str(empirical).lower(),
        "review_language_signal": str(review).lower(),
        "A_signal": str(a_signal).lower(),
        "B_signal": str(b_signal).lower(),
        "P_signal": str(p_signal).lower(),
        "H_signal": str(h_signal).lower(),
        "W_signal": str(w_signal).lower(),
        "shared_cost_language_signal": str(shared_cost).lower(),
        "candidate_A_to_P": str(a_signal and p_signal).lower(),
        "candidate_A_to_H": str(a_signal and h_signal).lower(),
        "candidate_B_to_H": str(b_signal and h_signal).lower(),
        "candidate_B_to_P": str(b_signal and p_signal).lower(),
        "candidate_joint_channels": str(a_signal and b_signal and p_signal and h_signal).lower(),
        "coding_warning": (
            "Keyword co-mention is an abstract-level candidate edge only; it does not establish a measured causal route, "
            "sign, effect magnitude, or model parameter value."
        ),
    }


def classify_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    return [classify_row(row) for row in rows]


def summarize_edges(records: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    records = list(records)
    success = [row for row in records if row["abstract_code_status"] == "coded_crossref_abstract"]
    floral = [row for row in success if is_true(row["floral_context_signal"])]
    output: list[dict[str, str]] = []
    for edge, (component, field) in EDGE_DEFINITIONS.items():
        subset = [row for row in records if is_true(row[field])]
        nonreview = [row for row in subset if not is_true(row["review_language_signal"])]
        empirical = [row for row in subset if is_true(row["empirical_language_signal"])]
        priority = [row for row in subset if row["shallow_screen_status"] == "priority_for_shallow_source_coding"]
        biological = [row for row in subset if row["shallow_screen_status"] == "biological_context_needs_route_screen"]
        if not subset:
            status = "no_abstract_candidate_edge_in_fixed_packet"
        elif len(subset) < 10:
            status = "very_sparse_abstract_candidate_coverage"
        else:
            status = "broad_abstract_candidate_coverage_present"
        output.append({
            "model_edge": edge,
            "model_component": component,
            "fixed_l1_records": str(len(records)),
            "abstract_retrieval_success_records": str(len(success)),
            "floral_context_abstract_records": str(len(floral)),
            "broad_edge_candidate_records": str(len(subset)),
            "nonreview_edge_candidate_records": str(len(nonreview)),
            "empirical_language_edge_candidate_records": str(len(empirical)),
            "priority_edge_candidate_records": str(len(priority)),
            "biological_context_edge_candidate_records": str(len(biological)),
            "coverage_status": status,
            "interpretation_boundary": (
                "Counts describe broad abstract-level candidate attention in a query-derived fixed corpus. They are not independent studies, "
                "effect sizes, direct-route confirmations, or parameter estimates."
            ),
        })
    return output


def write_outputs(out_dir: str | Path, records: Iterable[dict[str, str]], edges: Iterable[dict[str, str]]) -> None:
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    for filename, fields, rows in (
        ("broad_abstract_evidence_records.csv", RECORD_FIELDS, records),
        ("broad_abstract_edge_coverage.csv", EDGE_SUMMARY_FIELDS, edges),
    ):
        with (destination / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
