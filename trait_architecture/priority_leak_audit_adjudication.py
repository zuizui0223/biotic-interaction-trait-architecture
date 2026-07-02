"""Prepare and summarize direct-route coding for the priority-leak audit."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from trait_architecture.broad_source_screening import SOURCE_ACCESS_STATUSES, SOURCE_SCREEN_STATUSES

PACKET = (
    "audit_group","route_family_audit","audit_rank","candidate_id","doi","title",
    "publication_year","container_title","landing_page_url","source_queries","route_families",
    "metadata_A_signal","metadata_B_signal","metadata_P_signal","metadata_H_signal","metadata_W_signal",
    "metadata_biology_context_term_count","shallow_screen_status","shallow_screen_reason",
    "crossref_lookup_status","crossref_message_type","crossref_title","crossref_published_year",
    "crossref_container_title","crossref_abstract_available","crossref_abstract_text","source_packet_warning",
)
SOURCE = (
    "source_screen_status","source_access_status","study_type","taxon","primary_study_id",
    "study_cluster_id","screen_exclusion_reason",
)
FIELDS = (*PACKET,*SOURCE,"route_screen_status","route_screen_reason","source_locator","coder_id","coding_date","coding_note")
ROUTE_STATUS = frozenset({"unassessed","direct_route_present","direct_route_absent"})
SUMMARY_FIELDS = (
    "route_family_audit","audit_group","sampled_rows","route_screenable_rows",
    "direct_route_present_rows","direct_route_absent_rows","unassessed_rows",
    "completion_fraction","direct_route_yield",
)
COMPARISON_FIELDS = (
    "route_family_audit","priority_screenable_rows","priority_direct_route_present_rows",
    "priority_direct_route_yield","biological_nonpriority_screenable_rows",
    "biological_nonpriority_direct_route_present_rows","biological_nonpriority_direct_route_yield",
    "nonpriority_minus_priority_yield","comparison_status",
)
BOUNDARY = (
    "This route-stratified screen audit does not establish an effect, direction, causal design, "
    "quantitative eligibility, or corpus-wide prevalence."
)


def text(value):
    return str(value or "").strip()


def key(row):
    return tuple(text(row.get(field)) for field in PACKET[:4])


def read(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return [{k: text(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def check_packet(rows):
    seen = set()
    for row in rows:
        if not set(PACKET).issubset(row) or not all(key(row)) or key(row) in seen:
            raise ValueError("audit packet requires unique, complete audit identities")
        seen.add(key(row))


def make_sheet(packet_rows):
    packet_rows = list(packet_rows)
    check_packet(packet_rows)
    sheet = []
    for packet in packet_rows:
        row = {field: text(packet.get(field)) for field in PACKET}
        row.update({
            "source_screen_status": "unassessed",
            "source_access_status": "abstract_only" if row["crossref_abstract_available"] == "true" else "unassessed",
            "study_type": "", "taxon": "", "primary_study_id": "", "study_cluster_id": "",
            "screen_exclusion_reason": "", "route_screen_status": "unassessed",
            "route_screen_reason": "", "source_locator": "", "coder_id": "",
            "coding_date": "", "coding_note": "",
        })
        sheet.append(row)
    check_sheet(sheet, packet_rows)
    return sheet


def check_sheet(rows, packet_rows=None):
    rows = list(rows)
    seen, source_decisions = set(), {}
    for row in rows:
        ident = key(row)
        if not set(FIELDS).issubset(row) or not all(ident) or ident in seen:
            raise ValueError("audit coding sheet requires unique, complete audit identities")
        seen.add(ident)
        source, access, route = row["source_screen_status"], row["source_access_status"], row["route_screen_status"]
        if source not in SOURCE_SCREEN_STATUSES or access not in SOURCE_ACCESS_STATUSES or route not in ROUTE_STATUS:
            raise ValueError("invalid source/access/route screen status")
        decision = tuple(text(row[field]) for field in SOURCE)
        candidate = row["candidate_id"]
        if candidate in source_decisions and source_decisions[candidate] != decision:
            raise ValueError("shared candidate has inconsistent source-screen decisions")
        source_decisions[candidate] = decision
        inferred = ("study_type","taxon","primary_study_id","study_cluster_id","screen_exclusion_reason","route_screen_reason","source_locator")
        if source == "unassessed" and (route != "unassessed" or any(text(row[field]) for field in inferred)):
            raise ValueError("unassessed source rows cannot contain route/source decisions")
        if route != "unassessed":
            if source == "unassessed" or access in {"unassessed","inaccessible"}:
                raise ValueError("assessed route needs a usable source decision")
            if not text(row["route_screen_reason"]) or not text(row["source_locator"]):
                raise ValueError("assessed route needs a reason and locator")
        if source == "excluded" and (route != "direct_route_absent" or not text(row["screen_exclusion_reason"])):
            raise ValueError("excluded source needs absence decision and exclusion reason")
        if route == "direct_route_present":
            if source != "included_for_source_coding" or any(not text(row[field]) for field in ("study_type","primary_study_id","study_cluster_id")):
                raise ValueError("present route needs included source and traceable study identifiers")
    if packet_rows is not None:
        expected = {key(row): row for row in packet_rows}
        observed = {key(row): row for row in rows}
        if set(expected) != set(observed):
            raise ValueError("coding sheet does not cover exactly the frozen packet")
        for ident, raw in expected.items():
            if any(text(raw.get(field)) != text(observed[ident].get(field)) for field in PACKET):
                raise ValueError("coding sheet altered a frozen packet field")


def decimal(numerator, denominator):
    return "" if not denominator else f"{numerator / denominator:.6f}"


def summarize(rows):
    rows = list(rows)
    check_sheet(rows)
    counts = defaultdict(Counter)
    for row in rows:
        counts[(row["route_family_audit"],row["audit_group"])]["sampled_rows"] += 1
        counts[(row["route_family_audit"],row["audit_group"])][row["route_screen_status"]] += 1
    summary = []
    for (route, group), count in sorted(counts.items()):
        screenable = count["direct_route_present"] + count["direct_route_absent"]
        present = count["direct_route_present"]
        summary.append({
            "route_family_audit": route, "audit_group": group, "sampled_rows": str(count["sampled_rows"]),
            "route_screenable_rows": str(screenable), "direct_route_present_rows": str(present),
            "direct_route_absent_rows": str(count["direct_route_absent"]), "unassessed_rows": str(count["unassessed"]),
            "completion_fraction": decimal(screenable,count["sampled_rows"]), "direct_route_yield": decimal(present,screenable),
        })
    lookup = {(row["route_family_audit"],row["audit_group"]): row for row in summary}
    comparisons = []
    for route in sorted({route for route,_ in counts}):
        p, n = lookup[(route,"priority")], lookup[(route,"biological_nonpriority")]
        pn, nn = int(p["route_screenable_rows"]), int(n["route_screenable_rows"])
        py = int(p["direct_route_present_rows"]) / pn if pn else None
        ny = int(n["direct_route_present_rows"]) / nn if nn else None
        comparisons.append({
            "route_family_audit": route, "priority_screenable_rows": str(pn),
            "priority_direct_route_present_rows": p["direct_route_present_rows"],
            "priority_direct_route_yield": "" if py is None else f"{py:.6f}",
            "biological_nonpriority_screenable_rows": str(nn),
            "biological_nonpriority_direct_route_present_rows": n["direct_route_present_rows"],
            "biological_nonpriority_direct_route_yield": "" if ny is None else f"{ny:.6f}",
            "nonpriority_minus_priority_yield": "" if py is None or ny is None else f"{ny-py:.6f}",
            "comparison_status": "comparable_screened_groups" if pn and nn else "insufficient_screened_rows",
        })
    diagnostics = {
        "interpretation_boundary": BOUNDARY, "sampled_row_count": len(rows),
        "overall_route_screen_status_counts": dict(sorted(Counter(row["route_screen_status"] for row in rows).items())),
    }
    return summary, comparisons, diagnostics


def write_sheet(path, rows):
    rows = list(rows)
    check_sheet(rows)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(out_dir, summary, comparisons, diagnostics):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, fields, rows in (
        ("priority_leak_audit_yield_by_route_group.csv",SUMMARY_FIELDS,summary),
        ("priority_leak_audit_yield_comparisons.csv",COMPARISON_FIELDS,comparisons),
    ):
        with (out_dir / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    (out_dir / "priority_leak_audit_coding_diagnostics.json").write_text(
        json.dumps(diagnostics,indent=2,sort_keys=True),encoding="utf-8"
    )
