"""Probe whether GloBI can be treated as a plant-antagonist network backbone.

This is intentionally a *contract* test rather than an interaction analysis.
GloBI provides open, versioned interaction products and an API, but a record of
an insect eating a plant is not automatically a sampled local network. The
probe checks field-level capabilities and a small live query, then records
whether GloBI can advance to a network-backbone audit without reconstructing
original datasets.

Usage:
    python scripts/probe_globi_antagonist_contract.py out_dir
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


FIELD_URL = "https://api.globalbioticinteractions.org/interactionFields?type=json"
INTERACTION_URL = "https://api.globalbioticinteractions.org/interaction"
USER_AGENT = "biotic-interaction-trait-architecture GloBI contract probe/0.1"


def fetch_json(url: str) -> object:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:  # nosec B310: fixed public endpoint
        return json.loads(response.read().decode("utf-8"))


def capability_report(fields: dict[str, object]) -> dict[str, object]:
    """Map available GloBI fields to the project network contract.

    The result deliberately requires an explicit, unique network identifier and
    an effort/sampling denominator.  Study citation or a non-unique study title
    is valuable provenance, but not enough to promote a global interaction
    aggregator to a network backbone.
    """

    available = set(fields)
    return {
        "plant_and_animal_taxa": {
            "required_fields": ["source_taxon_name", "target_taxon_name", "interaction_type"],
            "available": {name: name in available for name in ["source_taxon_name", "target_taxon_name", "interaction_type"]},
        },
        "study_provenance": {
            "required_fields": ["study_source_id", "study_citation", "study_doi"],
            "available": {name: name in available for name in ["study_source_id", "study_citation", "study_doi"]},
        },
        "place_and_time": {
            "required_fields": ["latitude", "longitude", "event_date"],
            "available": {name: name in available for name in ["latitude", "longitude", "event_date"]},
        },
        "weight_or_count": {
            "candidate_fields": ["target_specimen_total_count", "target_specimen_frequency_of_occurrence"],
            "available": {
                name: name in available
                for name in ["target_specimen_total_count", "target_specimen_frequency_of_occurrence"]
            },
        },
        "network_identity": {
            "required_field": "network_id",
            "available": "network_id" in available,
            "non_substitute_field": "study_title" if "study_title" in available else None,
            "rule": "A non-unique study title cannot be silently used as a sampled network identifier.",
        },
        "sampling_effort": {
            "required_field": "sampling_effort_or_denominator",
            "available": any(name in available for name in ["sampling_effort", "sampling_protocol", "sampling_duration"]),
            "rule": "Counts or frequencies without a declared observation denominator do not establish comparable network effort.",
        },
    }


def main(out_dir: str) -> int:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "source": "GloBI public API",
        "purpose": "plant-antagonist network-contract feasibility test; not an ecological result",
        "query": {
            "sourceTaxon": "Insecta",
            "targetTaxon": "Plantae",
            "interactionType": "eats",
            "limit": 25,
        },
    }

    try:
        fields = fetch_json(FIELD_URL)
        if not isinstance(fields, dict):
            raise ValueError("interactionFields response is not a JSON object")
        report["field_capabilities"] = capability_report(fields)
        report["available_field_count"] = len(fields)
    except Exception as error:  # network/API availability itself is a feasibility finding
        report.update(
            {
                "access_status": "field_schema_query_failed",
                "message": str(error),
                "decision": "no_go_GloBI_schema_access_failure",
            }
        )
        (output / "globi_antagonist_contract_report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    query_url = f"{INTERACTION_URL}?{urlencode(report['query'])}"
    report["query_url"] = query_url
    try:
        interactions = fetch_json(query_url)
        if isinstance(interactions, list):
            report["live_query_status"] = "success"
            report["live_query_rows"] = len(interactions)
            report["live_query_row_keys"] = sorted(
                {key for row in interactions if isinstance(row, dict) for key in row}
            )
        else:
            report["live_query_status"] = "unexpected_payload"
            report["live_query_payload_type"] = type(interactions).__name__
    except Exception as error:
        report["live_query_status"] = "query_failed"
        report["live_query_message"] = str(error)

    network_identity = report["field_capabilities"]["network_identity"]["available"]  # type: ignore[index]
    effort = report["field_capabilities"]["sampling_effort"]["available"]  # type: ignore[index]
    provenance = report["field_capabilities"]["study_provenance"]["available"]  # type: ignore[index]
    place_time = report["field_capabilities"]["place_and_time"]["available"]  # type: ignore[index]

    if network_identity and effort and all(provenance.values()) and all(place_time.values()):
        report["decision"] = "advance_to_dataset_level_network_audit"
    else:
        report["decision"] = "no_go_GloBI_as_ready_multiplex_network_backbone"
        report["next_use"] = (
            "GloBI may remain a discovery and provenance index. A network analysis would require "
            "reconstructing explicitly sampled original datasets; do not pool API claims as networks."
        )

    (output / "globi_antagonist_contract_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/probe_globi_antagonist_contract.py out_dir")
    raise SystemExit(main(sys.argv[1]))
