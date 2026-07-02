"""Build shallow broad edge coverage and the fixed-model evidence interface.

Usage:
    python scripts/build_broad_abstract_theory_map.py \
      artifacts/broad_abstract_evidence/fixed_l1_abstract_packet.csv \
      empirical/broad_reality_evidence/broad_route_records.csv \
      artifacts/broad_abstract_evidence
"""

from __future__ import annotations

import argparse
from pathlib import Path

from trait_architecture.broad_abstract_evidence_map import (
    classify_rows,
    read_packet,
    summarize_edges,
    write_outputs,
)
from trait_architecture.theory_evidence_interface import (
    build_interface,
    read_rows,
    write_interface,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("abstract_packet_csv")
    parser.add_argument("route_records_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)

    packet = read_packet(args.abstract_packet_csv)
    records = classify_rows(packet)
    edges = summarize_edges(records)
    destination = Path(args.out_dir)
    write_outputs(destination, records, edges)
    routes = read_rows(args.route_records_csv, {"route", "study_cluster_id", "reported_direction", "record_status", "is_primary_sign_record"})
    interface = build_interface(edges, routes)
    write_interface(destination / "theory_parameter_evidence_status.csv", interface)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
