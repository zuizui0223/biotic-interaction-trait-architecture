"""Build a fixed-corpus full-text screen and effect-extraction packet.

Usage:
    python scripts/build_floral_trait_animal_response_meta_packet.py \
      fixed-map/broad_abstract_evidence_records.csv \
      fixed-map/fixed_l1_abstract_packet.csv \
      artifacts/floral_trait_animal_response_meta

The command never runs a new literature query. It broadens the *analysis
contract*, not the fixed candidate universe.
"""

from __future__ import annotations

import argparse

from trait_architecture.floral_trait_animal_response_meta import (
    PACKET_REQUIRED,
    RECORD_REQUIRED,
    build_candidate_queue,
    make_extraction_sheet,
    read_rows,
    write_candidate_packet,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_records_csv")
    parser.add_argument("abstract_packet_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)

    queue = build_candidate_queue(
        read_rows(args.evidence_records_csv, RECORD_REQUIRED),
        read_rows(args.abstract_packet_csv, PACKET_REQUIRED),
    )
    write_candidate_packet(args.out_dir, queue, make_extraction_sheet(queue))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
