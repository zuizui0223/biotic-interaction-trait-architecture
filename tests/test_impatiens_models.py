from trait_architecture.impatiens_models import design_matrix, prepare_rows


def raw_row(**updates: str) -> dict[str, str]:
    row = {
        "Pollinators_Per_Hour": "4",
        "Average_Percent_Florivory": "25",
        "Early_Season_Flower_Redness": "30",
        "Early_Season_Condensed_Tannins": "10",
        "Robbing": "N",
        "Florivory": "N",
        "Pollination": "Y",
        "Date_of_First_CH_Flower": "180",
    }
    row.update(updates)
    return row


def test_complete_case_preparation_omits_missing_declared_outcome() -> None:
    rows, omitted = prepare_rows(
        [raw_row(), raw_row(Pollinators_Per_Hour="")],
        outcome_field="Pollinators_Per_Hour",
        outcome_transform="log1p_then_zscore",
        attraction_field="Early_Season_Flower_Redness",
        attraction_transform="identity_then_zscore",
        barrier_field="Early_Season_Condensed_Tannins",
        barrier_transform="log1p_then_zscore",
        phenology_field="Date_of_First_CH_Flower",
    )

    assert len(rows) == 1
    assert omitted == 1
    assert rows[0]["Pollination_Y"] == 1.0


def test_design_matrix_adds_predeclared_interaction_only_when_requested() -> None:
    rows = [
        {"y": 1.0, "A": 1.0, "B": 1.0, "Robbing_Y": 0.0, "Florivory_Y": 0.0, "Pollination_Y": 0.0, "Phenology": 1.0},
        {"y": 2.0, "A": 2.0, "B": 3.0, "Robbing_Y": 1.0, "Florivory_Y": 0.0, "Pollination_Y": 1.0, "Phenology": 2.0},
        {"y": 3.0, "A": 4.0, "B": 2.0, "Robbing_Y": 0.0, "Florivory_Y": 1.0, "Pollination_Y": 0.0, "Phenology": 3.0},
    ]
    _, no_interaction, terms0 = design_matrix(rows, interaction=False)
    _, with_interaction, terms1 = design_matrix(rows, interaction=True)

    assert "A_z:B_z" not in terms0
    assert "A_z:B_z" in terms1
    assert len(with_interaction[0]) == len(no_interaction[0]) + 1
