from trait_architecture.broad_abstract_label_audit import (
    CONTROL_LABEL,
    EDGE_FIELDS,
    build_audit_packet,
    summarize_audit,
)


def make_record(candidate_id, *, edge=None, joint=False, empirical=True, review=False):
    flags = {field: "false" for field in EDGE_FIELDS.values()}
    if edge:
        flags[EDGE_FIELDS[edge]] = "true"
    if joint:
        flags[EDGE_FIELDS["joint_channels"]] = "true"
        for field in EDGE_FIELDS.values():
            flags[field] = "true"
    return {
        "candidate_id": candidate_id,
        "doi": f"10.test/{candidate_id}",
        "publication_year": "2024",
        "work_type": "journal-article",
        "route_families": edge or "none",
        "source_queries": "test",
        "shallow_screen_status": "priority_for_shallow_source_coding",
        "abstract_retrieval_state": "looked_up_from_fixed_candidate_doi",
        "crossref_lookup_status": "success",
        "crossref_abstract_available": "true",
        "abstract_code_status": "coded_crossref_abstract",
        "floral_context_signal": "true",
        "empirical_language_signal": str(empirical).lower(),
        "review_language_signal": str(review).lower(),
        "A_signal": "true", "B_signal": "true", "P_signal": "true", "H_signal": "true", "W_signal": "false",
        "shared_cost_language_signal": "false",
        **flags,
    }


def make_packet(record):
    return {
        "candidate_id": record["candidate_id"],
        "doi": record["doi"],
        "title": record["candidate_id"],
        "publication_year": "2024",
        "work_type": "journal-article",
        "container_title": "test journal",
        "publisher": "test publisher",
        "abstract_retrieval_state": "looked_up_from_fixed_candidate_doi",
        "crossref_lookup_status": "success",
        "crossref_abstract_available": "true",
        "crossref_abstract_text": "We measured floral traits, defence, pollination, and florivory.",
    }


def reviewed(row):
    return {
        **row,
        "coding_status": "reviewed",
        "coder_id": "test",
        "coding_date": "2026-07-02",
        "human_floral_context": "yes",
        "human_A": "yes",
        "human_B": "yes",
        "human_P": "yes",
        "human_H": "yes",
        "human_W": "no",
        "human_flower_specific_B": "yes",
        "human_study_role": "empirical_direct",
        "human_shared_cost": "no",
    }


def test_joint_is_censused_and_core_cells_keep_joint_population():
    records = [
        make_record("joint_emp", joint=True, empirical=True),
        make_record("joint_other", joint=True, empirical=False, review=True),
    ]
    for edge in ("A_to_pollination", "A_to_antagonism", "B_to_antagonism", "B_to_pollination"):
        records.extend(make_record(f"{edge}_{i}", edge=edge, empirical=(i % 2 == 0)) for i in range(6))
    records.extend(make_record(f"control_{i}", empirical=(i % 2 == 0)) for i in range(6))
    packet, coding, design = build_audit_packet(records, [make_packet(row) for row in records], nonjoint_target=3)

    by_label = {}
    for row in design:
        by_label.setdefault(row["target_label"], 0)
        by_label[row["target_label"]] += int(row["population_count"])
    assert by_label["joint_channels"] == 2
    assert by_label["B_to_antagonism"] == 8
    assert any("joint_channels__empirical_nonreview__joint_census" in row["audit_strata"] for row in packet)
    assert any(CONTROL_LABEL in row["audit_strata"] for row in packet)

    completion, precision, coverage, controls = summarize_audit([reviewed(row) for row in coding], design)
    coverage_by_edge = {row["target_label"]: row for row in coverage}
    assert completion[1]["value"] == str(len(coding))
    assert coverage_by_edge["joint_channels"]["raw_predicted_candidate_coverage"] == "2"
    assert coverage_by_edge["joint_channels"]["calibrated_candidate_coverage_mean"] == "2.000"
    assert all(row["calibration_status"] == "complete" for row in precision)
    assert all(row["calibration_status"] == "complete" for row in controls)


def test_incomplete_partitions_do_not_emit_calibrated_coverage():
    records = [make_record("ap", edge="A_to_pollination"), make_record("control")]
    packet, coding, design = build_audit_packet(records, [make_packet(row) for row in records], nonjoint_target=1)
    coding[0] = reviewed(coding[0])
    _, _, coverage, _ = summarize_audit(coding, design)
    ap = next(row for row in coverage if row["target_label"] == "A_to_pollination")
    assert ap["calibration_status"] == "incomplete"
    assert ap["calibrated_candidate_coverage_mean"] == ""
