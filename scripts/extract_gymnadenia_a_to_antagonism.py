"""Run the predeclared Gymnadenia total-scent to floral-herbivory model.

Usage:
    python scripts/extract_gymnadenia_a_to_antagonism.py \
      10.5061/dryad.dj40r \
      artifacts/gymnadenia_a_to_antagonism
"""

from __future__ import annotations

import argparse
import json

from trait_architecture.gymnadenia_a_to_antagonism import (
    extract_gymnadenia_a_to_antagonism,
    write_gymnadenia_a_to_antagonism_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_doi")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)
    report = extract_gymnadenia_a_to_antagonism(dataset_doi=args.dataset_doi)
    write_gymnadenia_a_to_antagonism_report(args.out_dir, report)
    print(json.dumps({
        "analysis": report["analysis"],
        "sample": report["sample"],
        "effect": report["effect"],
        "decision_boundary": report["decision_boundary"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
