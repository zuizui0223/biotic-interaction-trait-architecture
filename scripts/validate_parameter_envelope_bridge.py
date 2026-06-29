"""Validate whether four-path summaries can enter a Part I parameter envelope.

Usage:
    python scripts/validate_parameter_envelope_bridge.py \
      configs/four_path_parameter_envelope_contracts.json \
      artifacts/four_path_synthesis/four_path_scale_specific_summaries.csv \
      artifacts/parameter_envelope_bridge
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from trait_architecture.parameter_envelopes import (
    load_contracts,
    readiness_report_to_dict,
    validate_contracts,
)


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract_json")
    parser.add_argument("synthesis_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)

    readiness = validate_contracts(load_contracts(args.contract_json), _read_csv(args.synthesis_csv))
    report = readiness_report_to_dict(readiness)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "parameter_envelope_readiness.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
