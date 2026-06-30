import csv
from pathlib import Path


ROOT = Path(__file__).parents[1]
ATLAS = ROOT / "empirical" / "four_path_effects" / "EVIDENCE_STATUS_v0.csv"
REGISTRY = ROOT / "empirical" / "four_path_effects" / "four_path_effect_registry.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def test_v0_atlas_accounts_for_registered_effect_study_clusters() -> None:
    atlas = read_csv(ATLAS)
    registry = read_csv(REGISTRY)

    atlas_studies = {row["study_id"] for row in atlas}
    registry_studies = {row["study_id"] for row in registry}
    assert registry_studies.issubset(atlas_studies)

    verified = {
        row["study_id"]: row
        for row in atlas
        if row["evidence_status"] in {"verified_effect_panel", "verified_one_path_effect"}
    }
    assert set(verified) == registry_studies
    assert verified["Gorden_Adler_2018_Impatiens_capensis"]["registered_effect_roles"] == (
        "A_to_pollination;A_to_antagonism;B_to_antagonism;B_to_pollination"
    )
    assert verified["Gross_Sun_Schiestl_2016_Gymnadenia_odoratissima"]["registered_effect_roles"] == "A_to_antagonism"


def test_v0_atlas_preserves_the_two_non_extraction_stopping_boundaries() -> None:
    atlas = {row["study_id"]: row for row in read_csv(ATLAS)}

    impatiens_2016 = atlas["Gorden_Adler_2016_Impatiens_capensis"]
    assert impatiens_2016["evidence_status"] == "reported_table_screen_pending"
    assert "independent replication" in impatiens_2016["prohibited_inference"]

    rhellicani = atlas["Kellenberger_et_al_2019_Gymnadenia_rhellicani"]
    assert rhellicani["evidence_status"] == "verified_source_unidentified_visit_effect"
    assert "fruit, seed, or fitness" in rhellicani["prohibited_inference"]
