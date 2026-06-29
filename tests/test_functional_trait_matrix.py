from pathlib import Path

from trait_architecture.functional_trait_matrix import audit_functional_trait_matrix, audit_functional_trait_matrix_file


MATRIX_PATH = Path("empirical/functional_traits/trait_role_evidence.csv")


def test_initial_functional_trait_matrix_passes_protocol_audit() -> None:
    report = audit_functional_trait_matrix_file(MATRIX_PATH)

    assert report.is_valid, report.errors
    assert report.n_rows >= 20
    assert report.module_counts["A_flower"] >= 4
    assert report.module_counts["Q_leaf"] >= 4
    assert report.module_counts["B_leaf"] >= 4


def test_unresolved_trait_cannot_be_retained_for_v1() -> None:
    row = {
        "trait_id": "ambiguous_pattern",
        "trait_label": "ambiguous pattern",
        "organ": "leaf",
        "functional_module": "visual_leaf",
        "trait_modality": "visual",
        "candidate_consumer_layer": "leaf_herbivory",
        "mechanism_claim": "unknown",
        "evidence_grade": "U",
        "global_availability": "low",
        "provisional_role": "future case",
        "v1_decision": "hold_for_case_study",
        "source_seed_ids": "",
        "notes": "unresolved",
    }

    report = audit_functional_trait_matrix([row])

    assert not report.is_valid
    assert any("unresolved function" in error for error in report.errors)


def test_primary_trait_cannot_bypass_coverage_gate() -> None:
    row = {
        "trait_id": "primary_low_coverage",
        "trait_label": "primary low coverage",
        "organ": "leaf",
        "functional_module": "Q_leaf",
        "trait_modality": "leaf_economics",
        "candidate_consumer_layer": "leaf_herbivory",
        "mechanism_claim": "quality proxy",
        "evidence_grade": "B",
        "global_availability": "very_low",
        "provisional_role": "primary leaf quality candidate",
        "v1_decision": "retain_pending_coverage",
        "source_seed_ids": "CARMONA_2011",
        "notes": "invalid setup",
    }

    report = audit_functional_trait_matrix([row])

    assert not report.is_valid
    assert any("very_low availability" in error for error in report.errors)
