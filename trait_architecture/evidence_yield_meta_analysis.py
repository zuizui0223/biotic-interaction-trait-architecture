"""Calibrate L2 direct-route evidence yield from the frozen route-stratified audit."""

from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import NormalDist
from typing import Iterable

AUDIT_FIELDS = (
    "route_family_audit", "audit_group", "sampled_rows", "route_screenable_rows",
    "direct_route_present_rows", "direct_route_absent_rows", "unassessed_rows",
)
SCREEN_FIELDS = (
    "candidate_id", "route_families", "abstract_available", "shallow_screen_status",
)
ROUTE_GROUP_FIELDS = (
    "route", "audit_group", "l1_candidate_memberships", "l2_candidate_memberships",
    "l2_abstract_available_memberships", "audit_sampled_rows", "audit_screenable_rows",
    "audit_direct_route_rows", "audit_direct_route_yield", "posterior_model",
    "posterior_direct_rate_mean", "posterior_direct_rate_ci_low", "posterior_direct_rate_ci_high",
    "equal_yield_projection_mean", "equal_yield_projection_ci_low", "equal_yield_projection_ci_high",
    "abstract_proxy_projection_mean", "abstract_proxy_projection_ci_low",
    "abstract_proxy_projection_ci_high", "projection_boundary",
)
SCREEN_META_FIELDS = (
    "route", "priority_direct", "priority_non_direct", "nonpriority_direct",
    "nonpriority_non_direct", "continuity_correction", "log_odds_ratio", "standard_error",
    "included_in_random_effects", "status",
)
META_SUMMARY_FIELDS = (
    "analysis", "included_route_comparisons", "excluded_double_zero_routes", "pooled_log_odds_ratio",
    "pooled_odds_ratio", "pooled_standard_error", "ci_low_log_odds_ratio", "ci_high_log_odds_ratio",
    "ci_low_odds_ratio", "ci_high_odds_ratio", "tau_squared_DL", "Q", "Q_df", "I_squared_percent",
    "interpretation_boundary",
)
VALID_AUDIT_GROUPS = frozenset({"priority", "biological_nonpriority"})
SCREEN_GROUPS = {
    "priority": "priority_for_shallow_source_coding",
    "biological_nonpriority": "biological_context_needs_route_screen",
}
Z_975 = NormalDist().inv_cdf(0.975)


class EvidenceYieldInputError(ValueError):
    pass


def text(value: object) -> str:
    return str(value or "").strip()


def as_int(value: object, label: str) -> int:
    try:
        result = int(text(value))
    except ValueError as error:
        raise EvidenceYieldInputError(f"{label} must be an integer") from error
    if result < 0:
        raise EvidenceYieldInputError(f"{label} must be non-negative")
    return result


def is_true(value: object) -> bool:
    return text(value).lower() in {"true", "1", "yes", "y"}


def split_routes(value: object) -> list[str]:
    return [item for item in text(value).split(";") if item]


def read_rows(path: str | Path, required: Iterable[str]) -> list[dict[str, str]]:
    location = Path(path)
    with location.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(required).difference(reader.fieldnames or [])
        if missing:
            raise EvidenceYieldInputError(f"missing columns: {', '.join(sorted(missing))}")
        return [{key: text(value) for key, value in row.items()} for row in reader]


def validate_audit(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    rows = list(rows)
    observed: set[tuple[str, str]] = set()
    for row in rows:
        route, group = text(row.get("route_family_audit")), text(row.get("audit_group"))
        if not route or group not in VALID_AUDIT_GROUPS or (route, group) in observed:
            raise EvidenceYieldInputError("audit route/group cells must be unique and valid")
        observed.add((route, group))
        sampled = as_int(row.get("sampled_rows"), "sampled_rows")
        screenable = as_int(row.get("route_screenable_rows"), "route_screenable_rows")
        present = as_int(row.get("direct_route_present_rows"), "direct_route_present_rows")
        absent = as_int(row.get("direct_route_absent_rows"), "direct_route_absent_rows")
        unresolved = as_int(row.get("unassessed_rows"), "unassessed_rows")
        if sampled != screenable + unresolved or screenable != present + absent:
            raise EvidenceYieldInputError("audit counts do not reconcile")
    return rows


def screen_universe_counts(rows: Iterable[dict[str, str]]) -> dict[tuple[str, str], Counter[str]]:
    counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in rows:
        matched = [group for group, status in SCREEN_GROUPS.items() if text(row.get("shallow_screen_status")) == status]
        for route in split_routes(row.get("route_families")):
            for group in VALID_AUDIT_GROUPS:
                counts[(route, group)]["l1"] += 1
            for group in matched:
                counts[(route, group)]["l2"] += 1
                counts[(route, group)]["abstract_available"] += int(is_true(row.get("abstract_available")))
    return counts


def beta_samples(alpha: float, beta: float, seed: int, draws: int = 20000) -> list[float]:
    rng = random.Random(seed)
    return [rng.betavariate(alpha, beta) for _ in range(draws)]


def q025_q975(values: list[float]) -> tuple[float, float]:
    values = sorted(values)
    return values[round((len(values) - 1) * .025)], values[round((len(values) - 1) * .975)]
