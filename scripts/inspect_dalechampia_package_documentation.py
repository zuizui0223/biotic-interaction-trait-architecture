"""Write a bounded documentation-only inspection of the public *Dalechampia* archive.

Usage:
    python scripts/inspect_dalechampia_package_documentation.py \
      10.5061/dryad.0k6djh9xx \
      artifacts/dalechampia_linked_panel
"""

from __future__ import annotations

import argparse
import json

from trait_architecture.dalechampia_package_documentation import (
    inspect_package_documentation,
    write_documentation_inspection,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_doi")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)
    report = inspect_package_documentation(args.dataset_doi)
    write_documentation_inspection(args.out_dir, report)
    print(json.dumps({
        "dataset_doi": report["dataset_doi"],
        "documentation_record_count": report["documentation_record_count"],
        "decision_boundary": report["decision_boundary"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
