import math

import pytest

from trait_architecture.floral_trait_animal_response_meta import (
    FloralTraitResponseMetaError,
    build_candidate_queue,
    make_extraction_sheet,
    summarize_ready_groups,
    validate_effect_rows,
)


def record(candidate_id, **overrides):
    row = {
        "candidate_id": candidate_id,
        "doi": f"10.test/{candidate_id}",
        "publication_year": "2024",
        "work_type": "journal-article",
        "route_families": "A_to_pollination",
        "source_queries": "test",
        "shallow_screen_status": "priority_for_shallow_source_coding",
        "crossref_abstract_available": "true",
        "floral_context_signal": "true",
        "empirical_language_signal": "true",
        "review_language_signal": "false",
        "candidate_A_to_P": "false",
        "candidate_A_to_H": "false",
        "candidate_B_to_H": "false",
        "candidate_B_to_P": "false",
    }
    row.update(overrides)
    return row


def packet(candidate_id, abstract):
    return {
        "candidate_id": candidate_id,
        "doi": f"10.test/{candidate_id}",
        "title": candidate_id,
        "publication_year": "2024",
        "work_type": "journal-article",
        "container_title": "test journal",
        "publisher": "test publisher",
        "crossref_abstract_available": "true",
        "crossref_abstract_text": abstract,
    }


def included_effect(index, *, route="A_to_pollinator", design="direct_experiment", family="hedges_g", outcome="visitation_or_foraging"):
    trait = "A_flower" if route.startswith("A_") else "B_flower"
    partner = "pollinator" if route.endswith("pollinator") else "floral_antagonist"
    return {
        "candidate_id": f"c{index}", "route": route, "study_id": f"s{index}", "effect_id": f"e{index}",
        "species": "Testus floralis", "study_year": "2024", "trait_name": "display", "trait_role": trait,
        "organ_match": "flower_or_inflorescence", "trait_contrast_or_predictor": "high vs low",
        "partner_response": partner, "outcome_family": outcome, "study_design": design, "effect_family": family,
        "effect_estimate": str(0.1 * index), "effect_variance": "0.04", "sample_size_total": "40",
        "independent_study_id": f"study{index}", "is_primary_effect_for_study": "true",
        "full_text_inclusion": "included", "exclusion_reason": "", "source_locator": "p. 3", "extractor_id": "test",
        "extraction_note": "", "direction_convention": "test",
    }


def test_candidate_queue_keeps_all_routes_and_prioritises_only_screening_order():
    records = [
        record("ap", candidate_A_to_P="true"),
        record("bh", candidate_B_to_H="true", route_families="B_to_antagonism"),
        record("off", floral_context_signal="false", candidate_A_to_P="true"),
    ]
    packets = [
        packet("ap", "We experimentally manipulated flower display, measured visitation, and report mean values (n = 20)."),
        packet("bh", "We measured floral trichomes, florivory damage and their correlation coefficient (n = 30)."),
        packet("off", "Not a flower study."),
    ]
    queue = build_candidate_queue(records, packets)
    assert [row["candidate_id"] for row in queue] == ["ap", "bh"]
    assert queue[0]["screening_priority"] == "tier_1_direct_effect_candidate"
    assert queue[1]["screening_priority"] == "tier_2_association_effect_candidate"
    sheet = make_extraction_sheet(queue)
    assert {row["route"] for row in sheet} == {"A_to_pollinator", "B_to_antagonist"}
    assert next(row for row in sheet if row["route"] == "B_to_antagonist")["trait_role"] == "B_flower"


def test_included_effects_require_organ_match_and_design_metric_compatibility():
    bad_leaf = included_effect(1, route="B_to_antagonist")
    bad_leaf["organ_match"] = "leaf"
    with pytest.raises(FloralTraitResponseMetaError):
        validate_effect_rows([bad_leaf])

    bad_metric = included_effect(1, design="observational_association", family="hedges_g")
    with pytest.raises(FloralTraitResponseMetaError):
        validate_effect_rows([bad_metric])


def test_random_effects_summary_requires_independent_primary_effects_and_never_mixes_metrics():
    rows = [included_effect(index) for index in range(1, 6)]
    summaries = summarize_ready_groups(rows, minimum_independent_studies=5)
    assert len(summaries) == 1
    result = summaries[0]
    assert result.status == "ready_random_effects"
    assert result.independent_studies == 5
    assert math.isfinite(result.estimate)

    sparse = summarize_ready_groups(rows[:4], minimum_independent_studies=5)[0]
    assert sparse.status == "insufficient_independent_studies"
    assert math.isnan(sparse.estimate)
