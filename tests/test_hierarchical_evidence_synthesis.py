from trait_architecture.hierarchical_evidence_synthesis import build_hierarchical_summary


def test_hierarchical_summary_keeps_layers_separate():
    candidates = [
        {"candidate_id": "c1", "route_families": "A_to_pollination;B_to_pollination"},
        {"candidate_id": "c2", "route_families": "B_to_pollination"},
        {"candidate_id": "c3", "route_families": "B_to_antagonism"},
    ]
    screened = [
        {
            "candidate_id": "c1", "route_families": "A_to_pollination;B_to_pollination",
            "shallow_screen_status": "priority_for_shallow_source_coding",
        },
        {
            "candidate_id": "c2", "route_families": "B_to_pollination",
            "shallow_screen_status": "biological_context_needs_route_screen",
        },
        {
            "candidate_id": "c3", "route_families": "B_to_antagonism",
            "shallow_screen_status": "likely_nonbiological_retrieval_noise",
        },
    ]
    audit = [
        {
            "route_family_audit": "B_to_pollination", "audit_group": "priority",
            "sampled_rows": "3", "route_screenable_rows": "2",
            "direct_route_present_rows": "1", "direct_route_absent_rows": "1",
            "unassessed_rows": "1",
        },
        {
            "route_family_audit": "B_to_pollination", "audit_group": "biological_nonpriority",
            "sampled_rows": "2", "route_screenable_rows": "1",
            "direct_route_present_rows": "0", "direct_route_absent_rows": "1",
            "unassessed_rows": "1",
        },
    ]
    route_records = [
        {
            "record_id": "r1", "study_cluster_id": "s1", "route": "B_to_pollination",
            "trait_class": "chemical_barrier", "outcome_class": "visitation_rate",
            "design_class": "manipulation", "reported_direction": "negative",
        },
        {
            "record_id": "r2", "study_cluster_id": "s2", "route": "B_to_pollination",
            "trait_class": "chemical_barrier", "outcome_class": "pollinator_preference_or_foraging",
            "design_class": "manipulation", "reported_direction": "mixed",
        },
        {
            "record_id": "r3", "study_cluster_id": "s3", "route": "B_to_antagonism",
            "trait_class": "chemical_barrier", "outcome_class": "floral_damage_proportion",
            "design_class": "manipulation", "reported_direction": "negative",
        },
    ]
    effects = [
        {"effect_id": "e1", "study_cluster_id": "s1", "route": "B_to_pollination", "analysis_status": "included"},
        {"effect_id": "e2", "study_cluster_id": "s2", "route": "B_to_pollination", "analysis_status": "candidate"},
    ]
    fulltext = [
        {
            "queue_id": "q1", "study_cluster_id": "s1", "doi": "10.x/a",
            "outcome_layer": "flower_visitation", "comparability_cell": "chemical_visitation",
            "full_text_state": "not_yet_source_adjudicated", "analysis_action": "source_read",
        },
        {
            "queue_id": "q2", "study_cluster_id": "s2", "doi": "10.x/b",
            "outcome_layer": "foraging_or_preference", "comparability_cell": "chemical_foraging",
            "full_text_state": "not_yet_source_adjudicated", "analysis_action": "source_read",
        },
    ]

    layer_rows, direction_rows, summary = build_hierarchical_summary(
        candidates, screened, audit, route_records, effects, fulltext
    )
    by_route = {row["route"]: row for row in layer_rows}

    assert by_route["B_to_pollination"]["candidate_records"] == "2"
    assert by_route["B_to_pollination"]["priority_records"] == "1"
    assert by_route["B_to_pollination"]["biological_context_records"] == "1"
    assert by_route["B_to_pollination"]["audit_sampled_rows"] == "5"
    assert by_route["B_to_pollination"]["audit_direct_route_rows"] == "1"
    assert by_route["B_to_pollination"]["direction_study_clusters"] == "2"
    assert by_route["B_to_pollination"]["quantitative_effects"] == "1"
    assert by_route["B_to_pollination"]["fulltext_queue_records"] == "2"
    assert summary["b_to_p_readiness"]["verdict"] == "inspect compatible B-to-P effect strata before numerical synthesis"
    assert {row["reported_direction"] for row in direction_rows if row["route"] == "B_to_pollination"} == {"negative", "mixed"}


def test_hierarchical_summary_does_not_promote_blank_effect_rows():
    layer_rows, _, summary = build_hierarchical_summary(
        [], [], [], [],
        [{"effect_id": "template", "study_cluster_id": "", "route": "B_to_pollination", "analysis_status": ""}],
        [],
    )

    assert layer_rows[0]["quantitative_effects"] == "0"
    assert summary["b_to_p_readiness"]["quantitative_effects"] == 0
    assert summary["b_to_p_readiness"]["verdict"] == "full-text source resolution required before any B-to-P numerical synthesis"
