from __future__ import annotations

import json

import pytest

from trait_architecture.broad_reality_evidence import (
    harvest_crossref,
    read_query_registry,
    summary,
)


def queries() -> list[dict[str, str]]:
    return [
        {
            "query_id": "AP01",
            "route_family": "A_to_pollination",
            "query_text": "floral trait pollination",
            "primary_empirical_question": "A to P",
            "expected_contribution": "coverage",
        },
        {
            "query_id": "BH01",
            "route_family": "B_to_antagonism",
            "query_text": "floral defence florivory",
            "primary_empirical_question": "B to H",
            "expected_contribution": "coverage",
        },
    ]


def record(doi: str, title: str, abstract: str = "") -> dict[str, object]:
    return {
        "DOI": doi,
        "title": [title],
        "author": [{"given": "A", "family": "Author"}],
        "issued": {"date-parts": [[2020, 1, 1]]},
        "type": "journal-article",
        "container-title": ["Journal of Flowers"],
        "publisher": "Example Press",
        "URL": f"https://doi.org/{doi}",
        "is-referenced-by-count": 12,
        "abstract": abstract,
    }


def fake_request(_: str, params: dict[str, str]) -> dict[str, object]:
    query = params["query.bibliographic"]
    if query == "floral trait pollination":
        items = [record("10.1/shared", "Flower colour and pollinator visitation", "Flower colour affected pollination success.")]
    else:
        items = [
            record("10.1/shared", "Flower colour and pollinator visitation", "Flower colour affected pollination success."),
            record("10.1/defence", "Floral defence and florivory", "Floral defence lowered flower damage and increased fruit set."),
        ]
    return {"message": {"items": items, "total-results": 500}}


def test_harvest_deduplicates_and_retains_route_membership() -> None:
    candidates, reports = harvest_crossref(queries(), rows_per_query=200, request_json=fake_request)

    assert len(candidates) == 2
    shared = next(item for item in candidates if item.doi == "10.1/shared")
    assert shared.source_queries == {"AP01", "BH01"}
    assert shared.route_families == {"A_to_pollination", "B_to_antagonism"}
    assert shared.metadata_A_signal is True
    assert shared.metadata_P_signal is True
    assert all(row["status"] == "success" for row in reports)

    report = summary(candidates, reports)
    assert report["unique_candidate_count"] == 2
    assert report["raw_returned_records"] == 3
    assert report["metadata_signal_counts"]["A"] >= 1
    assert "not effect directions" in report["interpretation_boundary"]
    json.dumps(report)


def test_harvest_refuses_to_publish_partial_query_corpus() -> None:
    def failed_request(_: str, params: dict[str, str]) -> dict[str, object]:
        if params["query.bibliographic"] == "floral defence florivory":
            raise RuntimeError("temporary API failure")
        return fake_request(_, params)

    with pytest.raises(RuntimeError, match="Crossref broad corpus retrieval incomplete: BH01"):
        harvest_crossref(queries(), rows_per_query=200, request_json=failed_request)


def test_query_registry_rejects_duplicate_query_ids(tmp_path) -> None:
    registry = tmp_path / "queries.csv"
    registry.write_text(
        "query_id,route_family,query_text,primary_empirical_question,expected_contribution\n"
        "AP01,A_to_pollination,one,q,c\n"
        "AP01,A_to_pollination,two,q,c\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="query IDs must be unique"):
        read_query_registry(registry)
