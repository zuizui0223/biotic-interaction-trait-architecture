from trait_architecture.meta_analysis_intake import build_intake


def route_record(record_id, cluster, route, trait_role, trait_class, outcome, design, source_basis="crossref_deposited_abstract"):
    return {
        "record_id": record_id,
        "study_id": f"study_{record_id}",
        "study_cluster_id": cluster,
        "doi": f"10.test/{record_id}",
        "taxon": "Test plant",
        "route": route,
        "trait_role": trait_role,
        "trait_class": trait_class,
        "outcome_class": outcome,
        "design_class": design,
        "source_basis": source_basis,
        "reported_direction": "negative" if route.startswith("B_") else "positive",
        "is_primary_sign_record": "true",
        "record_status": "included_for_direction_map",
        "context_note": "test",
        "coder_id": "test",
        "coding_date": "2026-07-02",
    }


def stratum():
    return {
        "stratum_id": "BP_chemical_visitation_lrr_manipulation",
        "route": "B_to_pollination",
        "trait_class": "chemical_barrier",
        "outcome_class": "visitation_rate",
        "effect_metric": "log_response_ratio",
        "design_class": "manipulation",
        "min_clusters_exploratory": "3",
        "min_clusters_stability": "5",
        "expected_effect_direction": "negative",
        "part_i_parameter": "c_D",
        "interpretation": "test",
    }


def test_intake_requires_exact_cell_and_primary_source_before_effects():
    candidates = [
        {"candidate_id": "c1", "route_families": "B_to_pollination"},
        {"candidate_id": "c2", "route_families": "B_to_pollination"},
        {"candidate_id": "c3", "route_families": "A_to_pollination"},
    ]
    screened = [
        {"candidate_id": "c1", "route_families": "B_to_pollination", "shallow_screen_status": "priority_for_shallow_source_coding"},
        {"candidate_id": "c2", "route_families": "B_to_pollination", "shallow_screen_status": "biological_context_needs_route_screen"},
        {"candidate_id": "c3", "route_families": "A_to_pollination", "shallow_screen_status": "metadata_context_uncertain"},
    ]
    audit = [
        {
            "route_family_audit": "B_to_pollination", "audit_group": "priority", "sampled_rows": "2",
            "route_screenable_rows": "1", "direct_route_present_rows": "0",
            "direct_route_absent_rows": "1", "unassessed_rows": "1",
        }
    ]
    exact = route_record(
        "r1", "cluster_exact", "B_to_pollination", "B", "chemical_barrier", "visitation_rate", "manipulation"
    )
    nonmatching = route_record(
        "r2", "cluster_foraging", "B_to_pollination", "B", "chemical_barrier", "pollinator_preference_or_foraging", "manipulation"
    )
    gate_rows, intake, capacity, summary = build_intake(
        candidates, screened, audit, [exact, nonmatching], [stratum()], [],
        [{
            "queue_id": "Q1", "study_cluster_id": "cluster_exact", "doi": "10.test/r1",
            "outcome_layer": "flower_visitation", "comparability_cell": "chemical_visitation",
            "full_text_state": "not_yet_source_adjudicated", "analysis_action": "source_read",
        }],
    )

    by_record = {row["record_id"]: row for row in intake}
    assert by_record["r1"]["target_stratum_id"] == "BP_chemical_visitation_lrr_manipulation"
    assert by_record["r1"]["intake_status"] == "core_source_resolution_queue"
    assert by_record["r1"]["numeric_gate_status"] == "requires_primary_source_and_numeric_fields"
    assert by_record["r2"]["intake_status"] == "direction_map_only"
    assert by_record["r2"]["target_stratum_id"] == ""
    assert {row["gate_id"]: row for row in gate_rows}["G03"]["pass_count"] == "1"
    assert capacity[0]["direction_anchor_clusters"] == "1"
    assert capacity[0]["numeric_effect_clusters"] == "0"
    assert capacity[0]["capacity_status"] == "source_resolution_required"
    assert summary["input_counts"]["exact_predeclared_intake_anchors"] == 1


def test_primary_source_only_advances_to_numeric_field_check():
    primary = route_record(
        "r1", "cluster_exact", "B_to_pollination", "B", "chemical_barrier", "visitation_rate", "manipulation",
        source_basis="publisher_full_text",
    )
    _, intake, capacity, _ = build_intake(
        [], [], [], [primary], [stratum()], [], []
    )

    assert intake[0]["source_gate_status"] == "primary_source_confirmed"
    assert intake[0]["intake_status"] == "numeric_extraction_candidate"
    assert capacity[0]["primary_source_confirmed_clusters"] == "1"
    assert capacity[0]["numeric_effect_clusters"] == "0"
