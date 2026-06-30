"""Scout public sources for the Castilleja article without table extraction.

Usage:
    python scripts/scout_castilleja_public_sources.py artifacts/castilleja_public_sources
"""

from __future__ import annotations

import json
from pathlib import Path

from trait_architecture.public_article_source_scout import audit_study_sources, write_audit


ARTICLE_DOI = "10.1111/j.0030-1299.2004.12641.x"
QUEUE_ID = "Q006"
STUDY_ID = "Castilleja_linariaefolia_2004"


def main() -> int:
    receipts, report = audit_study_sources(
        study_doi=ARTICLE_DOI,
        queue_id=QUEUE_ID,
        study_id=STUDY_ID,
    )
    report["study_id"] = STUDY_ID
    write_audit(Path("artifacts/castilleja_public_sources"), receipts, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
