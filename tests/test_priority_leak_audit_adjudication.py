from trait_architecture.priority_leak_audit_adjudication import (
    PACKET,
    check_sheet,
    make_sheet,
    summarize,
)


def packet_row(candidate_id: str, group: str, route: str, rank: str = "1", abstract: str = "true") -> dict[str, str]:
    row = {field: "" for field in PACKET}
    row.update({
        "audit_group": group,
        "route_family_audit": route,
        "audit_rank": rank,
        "candidate_id": candidate_id,
        "doi": f"10.1000/{candidate_id}",
        "title": candidate_id,
        "crossref_lookup_status": "success",
        "crossref_abstract_available": abstract,
    })
    return row


def code_present(row: dict[str, str]) -> None:
    row.update({
        "source_screen_status": "included_for_source_coding",
        "source_access_status": "abstract_only",
        "study_type": "observational",
        "taxon": "Test plant",
        "primary_study_id": f"study_{row['candidate_id']}",
        "study_cluster_id": f"cluster_{row['candidate_id']}",
        "route_screen_status": "direct_route_present",
        "route_screen_reason": "Target trait and outcome are directly compared.",
        "source_locator": "Crossref deposited abstract",
        "coder_id": "tester",
        "coding_date": "2026-07-02",
    })


def code_absent(row: dict[str, str]) -> None:
    row.update({
        "source_screen_status": "included_for_source_coding",
        "source_access_status": "abstract_only",
        "study_type": "observational",
        "taxon": "Test plant",
        "primary_study_id": f"study_{row['candidate_id']}",
        "study_cluster_id": f"cluster_{row['candidate_id']}",
        "route_screen_status": "direct_route_absent",
        "route_screen_reason": "Usable source does not assess the target direct route.",
        "source_locator": "Crossref deposited abstract",
        "coder_id": "tester",
        "coding_date": "2026-07-02",
    })


def test_sheet_prefills_access_but_does_not_infer_decisions() -> None:
    packet = [
        packet_row("with_abstract", "priority", "A_to_pollination", abstract="true"),
        packet_row("without_abstract", "biological_nonpriority", "A_to_pollination", abstract="false"),
    ]
    sheet = make_sheet(packet)

    assert sheet[0]["source_access_status"] == "abstract_only"
    assert sheet[1]["source_access_status"] == "unassessed"
    assert {row["route_screen_status"] for row in sheet} == {"unassessed"}


def test_summary_excludes_unassessed_rows_from_yield() -> None:
    packet = [
        packet_row("p_present", "priority", "A_to_pollination", rank="1"),
        packet_row("p_uncoded", "priority", "A_to_pollination", rank="2"),
        packet_row("n_absent", "biological_nonpriority", "A_to_pollination", rank="1"),
        packet_row("n_present", "biological_nonpriority", "A_to_pollination", rank="2"),
    ]
    sheet = make_sheet(packet)
    code_present(sheet[0])
    code_absent(sheet[2])
    code_present(sheet[3])
    check_sheet(sheet, packet_rows=packet)

    summary, comparisons, diagnostics = summarize(sheet)
    priority = next(row for row in summary if row["audit_group"] == "priority")
    nonpriority = next(row for row in summary if row["audit_group"] == "biological_nonpriority")

    assert priority["route_screenable_rows"] == "1"
    assert priority["direct_route_yield"] == "1.000000"
    assert nonpriority["route_screenable_rows"] == "2"
    assert nonpriority["direct_route_yield"] == "0.500000"
    assert comparisons[0]["nonpriority_minus_priority_yield"] == "-0.500000"
    assert diagnostics["overall_route_screen_status_counts"]["unassessed"] == 1


def test_shared_candidate_requires_consistent_source_decision() -> None:
    packet = [
        packet_row("shared", "priority", "A_to_pollination"),
        packet_row("shared", "priority", "A_to_antagonism"),
    ]
    sheet = make_sheet(packet)
    code_present(sheet[0])

    try:
        check_sheet(sheet, packet_rows=packet)
    except ValueError as error:
        assert "inconsistent source-screen decisions" in str(error)
    else:
        raise AssertionError("expected shared candidate decision consistency error")
