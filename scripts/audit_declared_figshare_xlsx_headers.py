"""Write a header-only audit for an exact article-declared Figshare workbook."""

from __future__ import annotations

import argparse
import json

from trait_architecture.declared_figshare_xlsx_headers import (
    audit_declared_figshare_xlsx_headers,
    write_declared_figshare_xlsx_header_audit,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("figshare_article_id")
    parser.add_argument("file_name")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)
    report = audit_declared_figshare_xlsx_headers(
        figshare_article_id=args.figshare_article_id,
        file_name=args.file_name,
    )
    write_declared_figshare_xlsx_header_audit(args.out_dir, report)
    print(json.dumps({
        "file_name": report["file_name"],
        "sheet_count": report["sheet_count"],
        "decision_boundary": report["decision_boundary"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
