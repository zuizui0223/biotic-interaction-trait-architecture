"""Extract a bounded variable-definition dictionary from Impatiens archive docs.

This writes only documentation lines that explicitly mention predeclared
variables. It does not export data rows or calculate effects. The dictionary is
used to decide trait role, temporal precedence, response denominator, and
whether a four-path pre-analysis is identifiable.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from io import BytesIO
from pathlib import Path

from trait_architecture.dryad_archive_schema import _download_archive, _version_url
from trait_architecture.title_validated_dryad_manifest import probe_targets, read_targets


VARIABLES = (
    "Early_Season_Anthocyanins",
    "Early_Season_Condensed_Tannins",
    "Early_Season_Flower_Redness",
    "Pollinators_Per_Hour",
    "Average_Percent_Florivory",
    "Per_Florivory",
    "Tot_Flwrs",
    "Average_CH_Fruits_Per_Day",
    "Average_Seeds_Per_CH_Fruit",
    "Robbing",
    "Florivory",
    "Pollination",
)
MAX_MATCHES_PER_VARIABLE = 8
MAX_FRAGMENT_CHARS = 420


def _text(value: object) -> str:
    return str(value or "").strip()


def _find_receipt(targets: list[dict[str, str]]):
    receipts, manifest_report = probe_targets(targets)
    for receipt in receipts:
        if receipt.manifest_status == "manifest_recovered" and _version_url(receipt):
            return receipt, manifest_report
    raise RuntimeError("no title-validated Dryad archive was recovered")


def _fragment(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()[:MAX_FRAGMENT_CHARS]


def _matching_lines(text: str, variable: str) -> list[tuple[int, str]]:
    matches: list[tuple[int, str]] = []
    pattern = re.compile(rf"\b{re.escape(variable)}\b", re.IGNORECASE)
    for line_number, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            matches.append((line_number, _fragment(line)))
            if len(matches) >= MAX_MATCHES_PER_VARIABLE:
                break
    return matches


def extract(targets_csv: str, out_dir: str) -> dict[str, object]:
    targets = read_targets(targets_csv)
    receipt, manifest_report = _find_receipt(targets)
    archive_url = f"{_version_url(receipt)}/download"
    archive_bytes = _download_archive(archive_url, landing_page_url=receipt.landing_page_url)
    archive = zipfile.ZipFile(BytesIO(archive_bytes))

    records: list[dict[str, str]] = []
    for member in sorted(archive.infolist(), key=lambda item: item.filename):
        if member.is_dir() or not member.filename.lower().endswith(".txt"):
            continue
        document = archive.read(member).decode("utf-8", errors="replace")
        for variable in VARIABLES:
            for line_number, fragment in _matching_lines(document, variable):
                records.append({
                    "variable": variable,
                    "file_name": member.filename,
                    "line_number": str(line_number),
                    "fragment": fragment,
                })

    found = {record["variable"] for record in records}
    payload = {
        "study_id": receipt.study_id,
        "study_doi": receipt.study_doi,
        "dataset_doi": receipt.dataset_doi,
        "archive_url": archive_url,
        "manifest": manifest_report,
        "variable_definitions": records,
        "variables_without_documented_match": [variable for variable in VARIABLES if variable not in found],
        "warning": "Definition lines are documentation evidence only. They do not establish a biological trait role, a causal path, or a fitted effect estimate.",
    }
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "impatiens_variable_definition_dictionary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    return {
        "study_id": receipt.study_id,
        "dictionary_record_count": len(records),
        "variables_with_documented_match": len(found),
        "variables_without_documented_match": len(VARIABLES) - len(found),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)
    print(json.dumps(extract(args.targets_csv, args.out_dir), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
