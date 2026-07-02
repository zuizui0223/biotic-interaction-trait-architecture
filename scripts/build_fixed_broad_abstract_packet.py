"""Retrieve Crossref abstracts for an existing fixed L1 candidate table.

This does not issue new discovery queries and does not add candidate papers. It
looks up only DOI-backed rows that the original harvest already marked as having
an abstract.

Usage:
    python scripts/build_fixed_broad_abstract_packet.py \
      artifacts/broad_reality_evidence/broad_reality_evidence_screened.csv \
      artifacts/broad_abstract_evidence/fixed_l1_abstract_packet.csv
"""

from __future__ import annotations

import argparse

from trait_architecture.broad_abstract_corpus import (
    build_broad_abstract_packet,
    read_screened_candidates,
    write_broad_abstract_packet,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("screened_candidates_csv")
    parser.add_argument("out_csv")
    args = parser.parse_args(argv)
    packet = build_broad_abstract_packet(read_screened_candidates(args.screened_candidates_csv))
    write_broad_abstract_packet(args.out_csv, packet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
