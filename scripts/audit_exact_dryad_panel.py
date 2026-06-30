"""Audit an exact article-linked Dryad package without retaining observations.

Usage:
    python scripts/audit_exact_dryad_panel.py \
      10.1371/journal.pone.0147975 \
      10.5061/dryad.dj40r \
      Gymnadenia_odoratissima \
      artifacts/gymnadenia_exact_dryad_panel
"""

from __future__ import annotations

import argparse
import json

from trait_architecture.exact_dryad_panel_audit import (
    audit_exact_dryad_panel,
    write_exact_dryad_panel_audit,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("article_doi")
    parser.add_argument("dataset_doi")
    parser.add_argument("study_label")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)

    schemas, report = audit_exact_dryad_panel(
        article_doi=args.article_doi,
        dataset_doi=args.dataset_doi,
        study_label=args.study_label,
    )
    write_exact_dryad_panel_audit(
        args.out_dir,
        schemas,
        report,
        output_stem="exact_dryad_panel",
    )
    print(json.dumps({
        "study_label": report["study_label"],
        "dataset_doi": report["dataset_doi"],
        "article_relation_status": report["article_relation_status"],
        "header_recovered": report["schema"]["header_recovered"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
