"""Write aggregate manifests for exact declared Figshare image archives."""

from __future__ import annotations

import argparse
import json

from trait_architecture.declared_figshare_image_manifest import (
    audit_declared_figshare_image_manifests,
    write_declared_figshare_image_manifest_audit,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("figshare_article_id")
    parser.add_argument("out_dir")
    parser.add_argument("archive_name", nargs="+")
    args = parser.parse_args(argv)
    report = audit_declared_figshare_image_manifests(
        figshare_article_id=args.figshare_article_id,
        archive_names=args.archive_name,
    )
    write_declared_figshare_image_manifest_audit(args.out_dir, report)
    print(json.dumps({
        "figshare_article_id": report["figshare_article_id"],
        "archive_count": len(report["archives"]),
        "decision_boundary": report["decision_boundary"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
