"""Test whether Web of Life pollination edges can be oriented as plant--animal.

Web of Life's all-network endpoint provides `species1` and `species2` but does
not state which side is plant. This probe uses GBIF's public species-match API
on a bounded, reproducible sample from each side of each pollination network.

A successful result is a source-contract result only: it means the source can
advance to a trait-coverage test. It does not establish ecological inference.

Usage:
    python scripts/probe_wol_orientation.py out_dir
"""

from __future__ import annotations

import csv
import io
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

WOL_METADATA_URL = "https://www.web-of-life.es/get_network_info.php"
WOL_EDGES_URL = "https://www.web-of-life.es/get_networks.php"
GBIF_MATCH_URL = "https://api.gbif.org/v1/species/match"
USER_AGENT = "biotic-interaction-trait-architecture orientation probe/0.1"
SAMPLE_PER_SIDE_PER_NETWORK = 2


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:  # nosec B310: fixed public endpoints
        return response.read()


def match_gbif(name: str) -> dict[str, object]:
    query = urlencode({"name": name})
    payload = fetch(f"{GBIF_MATCH_URL}?{query}")
    return json.loads(payload.decode("utf-8"))


def kingdom_from_match(match: dict[str, object]) -> str:
    kingdom = str(match.get("kingdom", "")).strip()
    if kingdom in {"Plantae", "Animalia"}:
        return kingdom
    return "unresolved"


def side_evidence(names: list[str], cache: dict[str, str], audit_rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for name in names:
        if name not in cache:
            try:
                matched = match_gbif(name)
                cache[name] = kingdom_from_match(matched)
                audit_rows.append(
                    {
                        "taxon": name,
                        "kingdom": cache[name],
                        "match_type": str(matched.get("matchType", "")),
                        "confidence": str(matched.get("confidence", "")),
                        "status": str(matched.get("status", "")),
                        "canonical_name": str(matched.get("canonicalName", "")),
                    }
                )
                time.sleep(0.03)
            except Exception as exc:  # report source failure instead of guessing
                cache[name] = "unresolved"
                audit_rows.append(
                    {
                        "taxon": name,
                        "kingdom": "unresolved",
                        "match_type": "error",
                        "confidence": "",
                        "status": type(exc).__name__,
                        "canonical_name": "",
                    }
                )
        counts[cache[name]] += 1
    return counts


def orient(side1: Counter[str], side2: Counter[str]) -> str:
    # Require strictly more resolved evidence for the relevant kingdom on both
    # sides. Any mixed side remains ambiguous rather than silently orienting it.
    if side1["Plantae"] > side1["Animalia"] and side2["Animalia"] > side2["Plantae"]:
        return "species1_is_plant"
    if side2["Plantae"] > side2["Animalia"] and side1["Animalia"] > side1["Plantae"]:
        return "species2_is_plant"
    return "ambiguous"


def main(out_dir: str) -> int:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    metadata = list(csv.DictReader(io.StringIO(fetch(WOL_METADATA_URL).decode("utf-8-sig"))))
    edges = json.loads(fetch(WOL_EDGES_URL).decode("utf-8-sig"))
    pollination_networks = {row["network_name"] for row in metadata if row.get("network_type") == "Pollination"}
    per_network: dict[str, dict[str, set[str]]] = defaultdict(lambda: {"species1": set(), "species2": set()})
    for edge in edges:
        name = str(edge.get("network_name", ""))
        if name in pollination_networks:
            per_network[name]["species1"].add(str(edge.get("species1", "")).strip())
            per_network[name]["species2"].add(str(edge.get("species2", "")).strip())

    cache: dict[str, str] = {}
    taxon_audit: list[dict[str, str]] = []
    network_audit: list[dict[str, object]] = []
    for network_name in sorted(per_network):
        side1 = sorted(name for name in per_network[network_name]["species1"] if name)[:SAMPLE_PER_SIDE_PER_NETWORK]
        side2 = sorted(name for name in per_network[network_name]["species2"] if name)[:SAMPLE_PER_SIDE_PER_NETWORK]
        evidence1 = side_evidence(side1, cache, taxon_audit)
        evidence2 = side_evidence(side2, cache, taxon_audit)
        network_audit.append(
            {
                "network_name": network_name,
                "species1_sample": "; ".join(side1),
                "species2_sample": "; ".join(side2),
                "species1_plantae": evidence1["Plantae"],
                "species1_animalia": evidence1["Animalia"],
                "species1_unresolved": evidence1["unresolved"],
                "species2_plantae": evidence2["Plantae"],
                "species2_animalia": evidence2["Animalia"],
                "species2_unresolved": evidence2["unresolved"],
                "orientation": orient(evidence1, evidence2),
            }
        )

    orientation_counts = Counter(str(row["orientation"]) for row in network_audit)
    explicit = orientation_counts["species1_is_plant"] + orientation_counts["species2_is_plant"]
    sample_matched = sum(row["kingdom"] != "unresolved" for row in taxon_audit)
    report = {
        "source": "Web of Life + GBIF species match",
        "pollination_networks_seen": len(per_network),
        "sample_per_side_per_network": SAMPLE_PER_SIDE_PER_NETWORK,
        "unique_taxa_queried": len(taxon_audit),
        "gbif_resolved_taxon_rate": sample_matched / len(taxon_audit) if taxon_audit else 0.0,
        "orientation_counts": dict(sorted(orientation_counts.items())),
        "orientationable_network_rate": explicit / len(network_audit) if network_audit else 0.0,
        "decision": "advance_to_trait_coverage_test" if explicit / len(network_audit) >= 0.70 else "reject_or_repair_orientation_adapter",
        "rule": "At least 70% of pollination networks must be taxonomically orientable before plant-trait joins.",
    }
    (output / "wol_orientation_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    with (output / "wol_orientation_network_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(network_audit[0]))
        writer.writeheader()
        writer.writerows(network_audit)
    with (output / "wol_orientation_taxon_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["taxon", "kingdom", "match_type", "confidence", "status", "canonical_name"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(taxon_audit)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/probe_wol_orientation.py out_dir")
    raise SystemExit(main(sys.argv[1]))
