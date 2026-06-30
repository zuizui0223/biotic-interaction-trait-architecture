"""Verify unauthenticated Castilleja source access without table extraction."""

from __future__ import annotations

import json
from pathlib import Path

from trait_architecture.castilleja_access_probe import probe_castilleja_sources, write_probe


def main() -> int:
    receipts, report = probe_castilleja_sources()
    write_probe(Path("artifacts/castilleja_access_probe"), receipts, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
