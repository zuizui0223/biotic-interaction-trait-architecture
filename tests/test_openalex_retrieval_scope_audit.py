from __future__ import annotations

import json

import pytest

from trait_architecture import openalex_retrieval_scope_audit as scope
from trait_architecture.fixed_candidate_universe import CandidateSnapshotReceipt


def query_rows() -> list[dict[str, str]]:
    rows = []
    for query_id in sorted(scope.HISTORICAL_QUERY_IDS | scope.D_LEVEL_QUERY_IDS):
        rows.append({
            "query_id": query_id,
            "seed_route": f"route_{query_id}",
            "target_level": "D1" if query_id.startswith("D") else "M2",
            "query_text": f"query-{query_id}",
        })
    return rows


def work(query_id: str, index: int) -> dict[str, object]:
    return {
        "id": f"https://openalex.org/{query_id}_{index}",
        "display_name": f"{query_id} work {index}",
        "publication_year": 2020,
        "type": "article",
        "doi": f"https://doi.org/10.1000/{query_id}.{index}",
        "cited_by_count": index,
        "open_access": {"is_oa": True},
        "best_oa_location": {"pdf_url": f"https://example.org/{query_id}/{index}.pdf"},
    }


def fake_request(_: str, params: dict[str, str]) -> dict[str, object]:
    query_id = params["search"].removeprefix("query-")
    count = int(params["per-page"])
    return {
        "meta": {"count": 350},
        "results": [work(query_id, index) for index in range(count)],
    }


def fixed_loader():
    return (
        [{"candidate_id": "openalex:A01_0"}, {"candidate_id": "openalex:legacy_only"}],
        CandidateSnapshotReceipt(
            source_pr=20,
            source_workflow_run=1,
            source_artifact_id=2,
            source_member="fixed.csv",
            artifact_sha256="abc",
            candidate_count=258,
        ),
    )


def test_scope_audit_detects_depth_and_omitted_route_expansion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope, "load_fixed_candidate_universe", fixed_loader)

    results, candidates, report = scope.run_scope_audit(query_rows(), request_json=fake_request)

    assert len(results) == 10
    assert len(candidates) == 2000
    summary = report["summary"]
    counts = summary["current_result_counts"]
    assert counts["historical_six_query_top50_unique"] == 300
    assert counts["historical_six_query_top200_unique"] == 1200
    assert counts["historical_six_query_rank51_200_new_unique"] == 900
    assert counts["D01_to_D04_top200_unique"] == 800
    assert counts["D01_to_D04_not_in_current_historical_top200"] == 800
    assert summary["historical_snapshot_overlap"]["fixed_in_current_historical_top50"] == 1

    by_query = {row["query_id"]: row for row in report["query_report_rows"]}
    assert by_query["A01"]["new_ids_in_51_to_200"] == "150"
    assert by_query["A01"]["api_count_exceeds_200"] == "true"
    assert "current_historical_rank51_200" in {
        row["retrieval_strata"] for row in candidates if row["candidate_id"] == "openalex:A01_199"
    }
    json.dumps(report)


def test_scope_audit_requires_every_historical_and_d_query() -> None:
    incomplete = [row for row in query_rows() if row["query_id"] != "D04"]

    with pytest.raises(ValueError, match="missing scope-audit IDs: D04"):
        scope.run_scope_audit(incomplete, request_json=fake_request)
