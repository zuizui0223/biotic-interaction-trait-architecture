from trait_architecture.evidence_yield_meta_model import build_evidence_yield_meta


def audit(route, group, sampled, screenable, present):
    return {
        "route_family_audit": route,
        "audit_group": group,
        "sampled_rows": str(sampled),
        "route_screenable_rows": str(screenable),
        "direct_route_present_rows": str(present),
        "direct_route_absent_rows": str(screenable - present),
        "unassessed_rows": str(sampled - screenable),
    }


def screened(candidate_id, routes, status, abstract):
    return {
        "candidate_id": candidate_id,
        "route_families": routes,
        "shallow_screen_status": status,
        "abstract_available": abstract,
    }


def test_evidence_yield_uses_l2_memberships_and_keeps_double_zero_uninformative():
    screen = [
        screened("c1", "A_to_pollination;B_to_pollination", "priority_for_shallow_source_coding", "true"),
        screened("c2", "A_to_pollination", "priority_for_shallow_source_coding", "false"),
        screened("c3", "A_to_pollination", "biological_context_needs_route_screen", "true"),
        screened("c4", "B_to_pollination", "biological_context_needs_route_screen", "false"),
    ]
    audit_rows = [
        audit("A_to_pollination", "priority", 10, 8, 3),
        audit("A_to_pollination", "biological_nonpriority", 10, 5, 1),
        audit("B_to_pollination", "priority", 10, 8, 0),
        audit("B_to_pollination", "biological_nonpriority", 10, 5, 0),
    ]
    route_rows, effects, diagnostics, summary = build_evidence_yield_meta(screen, audit_rows)
    lookup = {(row["route"], row["audit_group"]): row for row in route_rows}
    effect_lookup = {row["route"]: row for row in effects}

    assert lookup[("A_to_pollination", "priority")]["l2_candidate_memberships"] == "2"
    assert lookup[("A_to_pollination", "priority")]["l2_abstract_available_memberships"] == "1"
    assert lookup[("B_to_pollination", "biological_nonpriority")]["l2_candidate_memberships"] == "1"
    assert float(lookup[("A_to_pollination", "priority")]["posterior_direct_rate_mean"]) > 0
    assert effect_lookup["B_to_pollination"]["status"] == "uninformative_double_zero_direct_yield"
    assert summary["included_route_comparisons"] == "1"
    assert diagnostics["audit_screenable_rows"] == 26


def test_evidence_yield_rejects_nonreconciling_audit_rows():
    bad = audit("A_to_pollination", "priority", 10, 8, 3)
    bad["unassessed_rows"] = "1"
    try:
        build_evidence_yield_meta([], [bad])
    except ValueError as error:
        assert "reconcile" in str(error)
    else:
        raise AssertionError("expected audit count validation error")
