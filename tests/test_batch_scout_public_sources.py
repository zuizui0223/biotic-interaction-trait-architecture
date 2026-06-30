import csv
from pathlib import Path

from trait_architecture.batch_public_source_scout import run


def write_candidates(path: Path) -> None:
    rows = [
        {
            "candidate_id": "openalex:W1", "seed_routes": "floral_damage_traits", "seed_query_ids": "Q1",
            "title": "Strong public route", "authors": "A", "publication_year": "2020", "publication_date": "2020-01-01",
            "work_type": "article", "doi": "10.1111/public", "landing_page_url": "", "open_access_url": "",
            "is_open_access": "true", "cited_by_count": "5", "metadata_match_score": "5",
            "metadata_attraction_signal": "true", "metadata_barrier_signal": "true",
            "metadata_pollination_signal": "true", "metadata_antagonist_signal": "true",
            "metadata_recoverability_signal": "true", "abstract_available": "true", "abstract_text": "",
            "candidate_status": "M0_candidate_needs_full_text", "metadata_warning": "",
        },
        {
            "candidate_id": "openalex:W2", "seed_routes": "floral_damage_traits", "seed_query_ids": "Q1",
            "title": "No public route", "authors": "B", "publication_year": "1999", "publication_date": "1999-01-01",
            "work_type": "article", "doi": "10.1111/closed", "landing_page_url": "", "open_access_url": "",
            "is_open_access": "false", "cited_by_count": "100", "metadata_match_score": "5",
            "metadata_attraction_signal": "true", "metadata_barrier_signal": "true",
            "metadata_pollination_signal": "true", "metadata_antagonist_signal": "true",
            "metadata_recoverability_signal": "false", "abstract_available": "true", "abstract_text": "",
            "candidate_status": "M0_candidate_needs_full_text", "metadata_warning": "",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_batch_scout_preserves_m0_and_ranks_public_leads(monkeypatch, tmp_path: Path) -> None:
    input_csv = tmp_path / "candidates.csv"
    out_dir = tmp_path / "out"
    write_candidates(input_csv)

    def fake_audit(study_doi: str, queue_id: str, study_id: str):
        from trait_architecture.public_article_source_scout import ArticleSourceReceipt

        receipts = [
            ArticleSourceReceipt(
                study_doi=study_doi, provider="Crossref", source_kind="article_metadata",
                resolution_status="metadata_recovered", request_url="", source_identifier="",
                title="", landing_page_url="", content_url="", content_type="",
                license_label="", relation_to_article="exact_article_doi", notes="",
            )
        ]
        if study_doi == "10.1111/public":
            receipts.append(ArticleSourceReceipt(
                study_doi=study_doi, provider="OpenAlex", source_kind="open_access_location",
                resolution_status="public_fulltext_candidate", request_url="", source_identifier="",
                title="", landing_page_url="", content_url="https://example.org/paper.pdf",
                content_type="application/pdf", license_label="", relation_to_article="exact_article_doi", notes="",
            ))
        return receipts, {}

    monkeypatch.setattr("trait_architecture.batch_public_source_scout.audit_study_sources", fake_audit)
    report = run(input_csv, out_dir, limit=0, sleep_seconds=0)

    assert report["screened_count"] == 2
    assert report["positive_lead_count"] == 1

    with (out_dir / "batch_public_source_positive_leads.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["candidate_id"] == "openalex:W1"
    assert rows[0]["automatic_evidence_level"] == "M0_public_source_lead_only"
    assert rows[0]["public_source_action"] == "inspect_public_full_text_for_methods_tables_and_supplements"
