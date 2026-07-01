"""Retrieve Crossref abstracts for the priority-leak audit queue.

Usage:
  python scripts/build_priority_leak_audit_abstract_packet.py INPUT_AUDIT_QUEUE.csv OUTPUT_PACKET.csv
"""

from __future__ import annotations

import argparse

from trait_architecture.priority_leak_audit_abstracts import (
    build_audit_abstract_packet,
    read_audit_queue,
    write_audit_abstract_packet,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit_queue_csv")
    parser.add_argument("output_csv")
    args = parser.parse_args(argv)

    packet = build_audit_abstract_packet(read_audit_queue(args.audit_queue_csv))
    write_audit_abstract_packet(args.output_csv, packet)
    available = sum(row["crossref_abstract_available"] == "true" for row in packet)
    failures = sum(row["crossref_lookup_status"] == "failed" for row in packet)
    print(f"audit_packet_rows={len(packet)} abstract_available={available} lookup_failures={failures}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
