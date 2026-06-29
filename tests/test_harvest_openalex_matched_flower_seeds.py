import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "harvest_openalex_matched_flower_seeds.py"
SPEC = importlib.util.spec_from_file_location("openalex_seed_harvest", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_reconstruct_abstract_orders_openalex_positions() -> None:
    abstract = MODULE.reconstruct_abstract({"pollination": [2], "floral": [0], "and": [1]})

    assert abstract == "floral and pollination"


def test_candidate_scoring_is_metadata_triage_not_evidence_classification() -> None:
    work = {
        "id": "https://openalex.org/W123",
        "display_name": "Floral scent, pollination and florivory",
        "publication_year": 2020,
        "publication_date": "2020-01-01",
        "type": "article",
        "doi": "https://doi.org/10.example/test",
        "authorships": [{"author": {"display_name": "A Author"}}],
        "cited_by_count": 5,
        "open_access": {"is_oa": True},
        "primary_location": {"landing_page_url": "https://example.org/article"},
        "best_oa_location": {"pdf_url": "https://example.org/article.pdf"},
        "abstract_inverted_index": {
            "individual": [0],
            "plants": [1],
            "received": [2],
            "pollinator": [3],
            "visitation": [4],
            "and": [5],
            "florivory": [6],
            "measurements": [7],
        },
    }

    candidate = MODULE.candidate_from_work(work, "A01", "floral_damage_traits")

    assert candidate.candidate_id == "openalex:W123"
    assert candidate.metadata_pollination_signal is True
    assert candidate.metadata_antagonist_signal is True
    assert candidate.metadata_recoverability_signal is True
    assert candidate.candidate_status == "M0_candidate_needs_full_text"
    assert "do not infer matched traits" in candidate.metadata_warning


def test_merge_retains_all_seed_routes_without_promoting_evidence_level() -> None:
    base = MODULE.Candidate(candidate_id="openalex:W1", title="candidate")
    other = MODULE.Candidate(
        candidate_id="openalex:W1",
        title="candidate",
        seed_routes={"route_b"},
        seed_query_ids={"B01"},
        metadata_antagonist_signal=True,
    )

    merged = MODULE.merge_candidate(base, other)

    assert merged.seed_routes == {"route_b"}
    assert merged.seed_query_ids == {"B01"}
    assert merged.metadata_antagonist_signal is True
    assert merged.candidate_status == "M0_candidate_needs_full_text"


def test_shortlist_uses_metadata_score_not_citation_count() -> None:
    high_match = MODULE.Candidate(
        candidate_id="openalex:match",
        title="match",
        seed_routes={"A"},
        metadata_match_score=4,
        cited_by_count=1,
    )
    highly_cited = MODULE.Candidate(
        candidate_id="openalex:cited",
        title="cited",
        seed_routes={"A"},
        metadata_match_score=1,
        cited_by_count=10000,
    )

    shortlist = MODULE.shortlist_by_route([highly_cited, high_match], 1)

    assert [item.candidate_id for item in shortlist] == ["openalex:match"]
