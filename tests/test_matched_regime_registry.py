from trait_architecture.matched_regime_registry import audit_matched_study_cards


COLUMNS = [
    "source_id",
    "seed_route",
    "source_type",
    "citation_or_doi",
    "full_text_status",
    "linked_data_status",
    "study_landscape_id",
    "region",
    "site_id",
    "sampling_period",
    "unit_of_linkage",
    "plant_taxon_scope",
    "attraction_trait_ids",
    "barrier_trait_ids",
    "module_separation_status",
    "pollination_response",
    "pollination_denominator",
    "pollination_same_context",
    "antagonist_response",
    "antagonist_denominator",
    "antagonist_same_context",
    "site_time_alignment",
    "attraction_to_pollination_status",
    "attraction_to_antagonist_status",
    "barrier_to_antagonist_status",
    "barrier_to_pollination_status",
    "fitness_response",
    "fitness_denominator",
    "shared_cost_status",
    "raw_table_status",
    "trait_method_status",
    "phylogeny_or_population_structure_status",
    "extraction_status",
    "notes",
]


def card(source_id: str, **overrides: str) -> dict[str, str]:
    row = {column: "" for column in COLUMNS}
    row.update(
        {
            "source_id": source_id,
            "seed_route": "A",
            "source_type": "article",
            "citation_or_doi": "10.example/test",
            "full_text_status": "read",
            "linked_data_status": "repository",
            "study_landscape_id": "landscape_1",
            "region": "region",
            "site_id": "site_1",
            "sampling_period": "2024-05",
            "unit_of_linkage": "individual",
            "plant_taxon_scope": "one species",
            "attraction_trait_ids": "flower_size",
            "barrier_trait_ids": "floral_chemical_defence",
            "module_separation_status": "independent",
            "pollination_response": "pollen_transfer",
            "pollination_denominator": "flowers_observed",
            "pollination_same_context": "yes",
            "antagonist_response": "florivory_damage",
            "antagonist_denominator": "flowers_inspected",
            "antagonist_same_context": "yes",
            "site_time_alignment": "exact",
            "attraction_to_pollination_status": "estimated",
            "attraction_to_antagonist_status": "estimated",
            "barrier_to_antagonist_status": "estimated",
            "barrier_to_pollination_status": "estimated",
            "fitness_response": "viable_seed_output",
            "fitness_denominator": "marked_flowers",
            "shared_cost_status": "estimated",
            "raw_table_status": "repository",
            "trait_method_status": "reported",
            "phylogeny_or_population_structure_status": "not_applicable",
            "extraction_status": "not_started",
        }
    )
    row.update(overrides)
    return row


def test_complete_card_is_a_parameterized_score_candidate() -> None:
    report = audit_matched_study_cards([card("D3")])
    summary = report.summaries[0]

    assert summary.evidence_level == "D3_parameterized_score_candidate"
    assert summary.missing_for_d1 == ()
    assert summary.missing_for_d2 == ()
    assert summary.missing_for_d3 == ()
    assert summary.high_information is True


def test_four_arrows_without_fitness_are_a_d1_channel_candidate() -> None:
    report = audit_matched_study_cards(
        [card("D1", fitness_response="not_observed", fitness_denominator="", shared_cost_status="not_estimated")]
    )
    summary = report.summaries[0]

    assert summary.evidence_level == "D1_channel_mechanism_candidate"
    assert summary.missing_for_d1 == ()
    assert "total reproductive-fitness response" in summary.missing_for_d2


def test_fitness_surface_without_shared_cost_is_a_d2_candidate() -> None:
    report = audit_matched_study_cards([card("D2", shared_cost_status="not_estimated")])
    summary = report.summaries[0]

    assert summary.evidence_level == "D2_observed_fitness_surface_candidate"
    assert summary.missing_for_d2 == ()
    assert "shared A_flower × B_flower cost/allocation estimate" in summary.missing_for_d3


def test_aligned_panel_without_all_four_paths_stays_m2() -> None:
    report = audit_matched_study_cards(
        [card("M2", barrier_to_pollination_status="not_estimated")]
    )
    summary = report.summaries[0]

    assert summary.evidence_level == "M2_aligned_two_channel_panel"
    assert "B_flower → pollination effect" in summary.missing_for_d1


def test_conflated_attraction_and_barrier_composite_stays_m2() -> None:
    report = audit_matched_study_cards(
        [card("conflated", module_separation_status="conflated_composite")]
    )
    summary = report.summaries[0]

    assert summary.evidence_level == "M2_aligned_two_channel_panel"
    assert "independent A_flower and B_flower measurement" in summary.missing_for_d1
    assert "Attraction and barrier measures are not independent" in summary.warnings[0]


def test_aligned_channels_without_recoverable_table_stay_m2() -> None:
    report = audit_matched_study_cards([card("M2_table", raw_table_status="not_found")])
    summary = report.summaries[0]

    assert summary.evidence_level == "M2_aligned_two_channel_panel"
    assert "recoverable linked table" in summary.missing_for_d1


def test_unaligned_channels_are_not_promoted_to_m2() -> None:
    report = audit_matched_study_cards([card("unaligned", antagonist_same_context="no")])
    summary = report.summaries[0]

    assert summary.evidence_level == "M1_channels_not_aligned"
    assert "antagonist same-context confirmation" in summary.missing_for_d1


def test_one_channel_card_is_not_a_direct_test() -> None:
    report = audit_matched_study_cards(
        [card("M1", antagonist_response="", antagonist_denominator="", barrier_trait_ids="")]
    )
    summary = report.summaries[0]

    assert summary.evidence_level == "M1_single_channel_ledger"
    assert "floral barrier/resistance trait" in summary.missing_for_d1
    assert "floral-antagonist response" in summary.missing_for_d1


def test_metadata_only_card_requires_full_text() -> None:
    report = audit_matched_study_cards(
        [card("M0", full_text_status="not_read", attraction_trait_ids="", barrier_trait_ids="")]
    )
    summary = report.summaries[0]

    assert summary.evidence_level == "M0_candidate_needs_full_text"
    assert "Full text has not been read" in summary.warnings[0]


def test_duplicate_source_id_is_counted_as_invalid() -> None:
    report = audit_matched_study_cards([card("duplicate"), card("duplicate")])

    assert report.invalid_cards == 1
    assert report.counts_by_level["D3_parameterized_score_candidate"] == 1
