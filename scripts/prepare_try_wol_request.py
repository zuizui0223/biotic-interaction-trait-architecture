"""Prepare a reproducible TRY species-request manifest from Web of Life.

This script does not request any trait values. It transforms the live Web of
Life pollination layer plus its already-tested plant-side orientation into a
species manifest for a human-submitted TRY request. The raw taxon spelling is
retained deliberately: TRY's own accepted-name reconciliation remains the
source of truth for the requested trait export.

Usage:
    python scripts/prepare_try_wol_request.py orientation_dir out_dir
"""

from __future__ import annotations

import csv
import io
import json
import sys
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

WOL_EDGES_URL = "https://www.web-of-life.es/get_networks.php"
USER_AGENT = "biotic-interaction-trait-architecture TRY request manifest/0.1"


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:  # nosec B310: fixed public endpoint
        return response.read()


def species_like(name: str) -> bool:
    parts = name.split()
    forbidden = {"sp.", "spp.", "cf.", "aff.", "indet."}
    return len(parts) >= 2 and all(part.lower() not in forbidden for part in parts)


def as_number(value: object) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def main(orientation_dir: str, out_dir: str) -> int:
    orientation_path = Path(orientation_dir) / "wol_orientation_network_audit.csv"
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    if not orientation_path.exists():
        raise RuntimeError("orientation audit is required before preparing TRY manifest")

    orientation_rows = list(csv.DictReader(orientation_path.open(encoding="utf-8")))
    orientation = {
        row["network_name"]: row["orientation"]
        for row in orientation_rows
        if row.get("orientation") in {"species1_is_plant", "species2_is_plant"}
    }
    edges = json.loads(fetch(WOL_EDGES_URL).decode("utf-8-sig"))

    summary: dict[str, dict[str, object]] = defaultdict(
        lambda: {"network_names": set(), "edge_count": 0, "weight_sum": 0.0}
    )
    for edge in edges:
        network_name = str(edge.get("network_name", "")).strip()
        side = orientation.get(network_name)
        if side is None:
            continue
        taxon = str(edge.get("species1" if side == "species1_is_plant" else "species2", "")).strip()
        if not taxon:
            continue
        entry = summary[taxon]
        entry["network_names"].add(network_name)
        entry["edge_count"] += 1
        entry["weight_sum"] += as_number(edge.get("connection_strength"))

    fieldnames = [
        "plant_taxon_as_reported",
        "name_looks_species_rank",
        "pollination_network_count",
        "weighted_edge_count",
        "interaction_weight_sum",
        "network_names",
        "try_status",
    ]
    rows = []
    for taxon in sorted(summary):
        entry = summary[taxon]
        network_names = sorted(entry["network_names"])
        rows.append(
            {
                "plant_taxon_as_reported": taxon,
                "name_looks_species_rank": str(species_like(taxon)).lower(),
                "pollination_network_count": len(network_names),
                "weighted_edge_count": entry["edge_count"],
                "interaction_weight_sum": f"{entry['weight_sum']:.12g}",
                "network_names": "; ".join(network_names),
                "try_status": "to_submit",
            }
        )

    manifest_path = output / "try_wol_pollination_species_request.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "source": "Web of Life pollination edges + oriented plant side",
        "oriented_pollination_networks": len(orientation),
        "unique_reported_plant_taxa": len(rows),
        "species_rank_like_taxa": sum(row["name_looks_species_rank"] == "true" for row in rows),
        "purpose": "manifest for a TRY trait-data request; not a trait table and not an ecological result",
        "requested_trait_modules": {
            "essential_attraction": [
                "flower colour / color",
                "flower or corolla size metrics",
                "inflorescence extent or flower number",
            ],
            "optional_reward_and_phenology": [
                "nectar volume or sugar concentration",
                "flowering onset and duration",
            ],
            "future_defence_module": [
                "leaf thickness",
                "leaf dry matter content",
                "leaf fracture toughness",
                "leaf area",
            ],
        },
        "excluded_circular_variable": "pollination syndrome",
    }
    (output / "try_wol_request_manifest_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python scripts/prepare_try_wol_request.py orientation_dir out_dir")
    raise SystemExit(main(sys.argv[1], sys.argv[2]))