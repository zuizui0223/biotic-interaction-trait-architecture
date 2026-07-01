"""Create a Crossref abstract source packet for the broad calibration queue."""

from __future__ import annotations

import argparse

from trait_architecture.broad_calibration_abstracts import (
    build_abstract_packet,
    read_calibration_batch,
    write_abstract_packet,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("calibration_batch_csv")
    parser.add_argument("output_csv")
    args = parser.parse_args(argv)

    packet = build_abstract_packet(read_calibration_batch(args.calibration_batch_csv))
    write_abstract_packet(args.output_csv, packet)
    available = sum(row["crossref_abstract_available"] == "true" for row in packet)
    failures = sum(row["crossref_lookup_status"] != "success" for row in packet)
    print(f"calibration_packet_rows={len(packet)} abstract_available={available} lookup_failures={failures}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
