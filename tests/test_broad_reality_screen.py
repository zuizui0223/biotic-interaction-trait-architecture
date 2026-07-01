from trait_architecture.broad_reality_screen import screen_row, screen_rows, screen_summary


def row(**overrides: str) -> dict[str, str]:
    value = {
        "title": "Floral scent and pollinator visitation in a plant species",
        "container_title": "Plant Ecology",
        "route_families": "A_to_pollination",
        "metadata_A_signal": "true",
        "metadata_B_signal": "false",
        "metadata_P_signal": "true",
        "metadata_H_signal": "false",
        "metadata_W_signal": "false",
    }
    value.update(overrides)
    return value


def test_priority_screen_requires_biology_context_trait_and_outcome() -> None:
    screened = screen_row(row())

    assert screened["shallow_screen_status"] == "priority_for_shallow_source_coding"
    assert int(screened["metadata_biology_context_term_count"]) >= 2
    assert screened["metadata_nonbiology_exclusion_signal"] == "false"


def test_nonbiological_flower_pollination_algorithm_is_excluded_before_priority() -> None:
    screened = screen_row(row(
        title="Flower pollination algorithm for feature selection",
        container_title="Computational Optimization",
    ))

    assert screened["shallow_screen_status"] == "likely_nonbiological_retrieval_noise"
    assert "algorithm" in screened["shallow_screen_reason"]


def test_context_only_record_does_not_become_priority_without_trait_signal() -> None:
    screened = screen_row(row(
        title="Pollination and reproductive success in a flowering plant",
        metadata_A_signal="false",
        metadata_P_signal="true",
        metadata_W_signal="true",
    ))

    assert screened["shallow_screen_status"] == "biological_context_needs_route_screen"


def test_screen_summary_counts_only_priority_records() -> None:
    screened = screen_rows([
        row(),
        row(title="Flower pollination algorithm", container_title="Optimization"),
        row(title="Pollination and reproductive success in a flowering plant", metadata_A_signal="false", metadata_W_signal="true"),
    ])
    summary = screen_summary(screened)

    assert summary["input_candidate_count"] == 3
    assert summary["priority_shallow_source_coding_count"] == 1
    assert summary["priority_route_family_counts"] == {"A_to_pollination": 1}
    assert "triage aid" in summary["interpretation_boundary"]
