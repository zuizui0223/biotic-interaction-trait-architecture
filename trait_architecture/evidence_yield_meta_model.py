"""Calibrated evidence-yield model and screen-rule random-effects meta-analysis."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Iterable

from trait_architecture.evidence_yield_meta_analysis import (
    META_SUMMARY_FIELDS,
    ROUTE_GROUP_FIELDS,
    SCREEN_META_FIELDS,
    VALID_AUDIT_GROUPS,
    Z_975,
    as_int,
    beta_samples,
    q025_q975,
    screen_universe_counts,
    validate_audit,
)


def _fit_group_prior(audit_rows: list[dict[str, str]], group: str) -> tuple[float, float]:
    """Deterministic empirical-Bayes beta prior for one L2 screen group."""
    cells = [row for row in audit_rows if row["audit_group"] == group]
    means = sorted({0.001, *[i / 1000 for i in range(2, 101, 2)], *[i / 100 for i in range(12, 51, 2)]})
    concentrations = [10 ** (-1.5 + 0.05 * step) for step in range(91)]
    best: tuple[float, float, float] | None = None
    for mean in means:
        for concentration in concentrations:
            alpha, beta = mean * concentration, (1 - mean) * concentration
            log_likelihood = 0.0
            for row in cells:
                y = as_int(row["direct_route_present_rows"], "direct_route_present_rows")
                n = as_int(row["route_screenable_rows"], "route_screenable_rows")
                log_likelihood += (
                    math.lgamma(alpha + y) + math.lgamma(beta + n - y)
                    - math.lgamma(alpha + beta + n)
                    - math.lgamma(alpha) - math.lgamma(beta) + math.lgamma(alpha + beta)
                )
            if best is None or log_likelihood > best[0]:
                best = (log_likelihood, alpha, beta)
    if best is None:
        raise ValueError("empirical-Bayes fit failed")
    return best[1], best[2]


def priority_screen_meta(audit_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, str]]:
    """Random-effects log-odds-ratio meta-analysis of screening enrichment."""
    lookup = {(row["route_family_audit"], row["audit_group"]): row for row in audit_rows}
    effects: list[tuple[float, float]] = []
    output: list[dict[str, str]] = []
    routes = sorted({route for route, _ in lookup})
    for route in routes:
        priority = lookup[(route, "priority")]
        nonpriority = lookup[(route, "biological_nonpriority")]
        a = as_int(priority["direct_route_present_rows"], "priority direct")
        b = as_int(priority["direct_route_absent_rows"], "priority non-direct")
        c = as_int(nonpriority["direct_route_present_rows"], "nonpriority direct")
        d = as_int(nonpriority["direct_route_absent_rows"], "nonpriority non-direct")
        if a == 0 and c == 0:
            output.append({
                "route": route, "priority_direct": str(a), "priority_non_direct": str(b),
                "nonpriority_direct": str(c), "nonpriority_non_direct": str(d),
                "continuity_correction": "0", "log_odds_ratio": "", "standard_error": "",
                "included_in_random_effects": "false", "status": "uninformative_double_zero_direct_yield",
            })
            continue
        correction = 0.5 if min(a, b, c, d) == 0 else 0.0
        aa, bb, cc, dd = a + correction, b + correction, c + correction, d + correction
        effect = math.log((aa * dd) / (bb * cc))
        variance = 1 / aa + 1 / bb + 1 / cc + 1 / dd
        effects.append((effect, variance))
        output.append({
            "route": route, "priority_direct": str(a), "priority_non_direct": str(b),
            "nonpriority_direct": str(c), "nonpriority_non_direct": str(d),
            "continuity_correction": f"{correction:.1f}", "log_odds_ratio": f"{effect:.6f}",
            "standard_error": f"{math.sqrt(variance):.6f}", "included_in_random_effects": "true",
            "status": "included",
        })
    if not effects:
        return output, {field: "" for field in META_SUMMARY_FIELDS}
    values, variances = zip(*effects)
    weights = [1 / value for value in variances]
    fixed = sum(weight * value for weight, value in zip(weights, values)) / sum(weights)
    q = sum(weight * (value - fixed) ** 2 for weight, value in zip(weights, values))
    df = len(values) - 1
    c_value = sum(weights) - sum(weight * weight for weight in weights) / sum(weights)
    tau = max(0.0, (q - df) / c_value) if c_value > 0 else 0.0
    random_weights = [1 / (variance + tau) for variance in variances]
    pooled = sum(weight * value for weight, value in zip(random_weights, values)) / sum(random_weights)
    se = math.sqrt(1 / sum(random_weights))
    low, high = pooled - Z_975 * se, pooled + Z_975 * se
    i2 = max(0.0, (q - df) / q * 100) if q > 0 and df > 0 else 0.0
    return output, {
        "analysis": "priority_vs_biological_nonpriority_direct_yield",
        "included_route_comparisons": str(len(values)),
        "excluded_double_zero_routes": str(len(output) - len(values)),
        "pooled_log_odds_ratio": f"{pooled:.6f}", "pooled_odds_ratio": f"{math.exp(pooled):.6f}",
        "pooled_standard_error": f"{se:.6f}", "ci_low_log_odds_ratio": f"{low:.6f}",
        "ci_high_log_odds_ratio": f"{high:.6f}", "ci_low_odds_ratio": f"{math.exp(low):.6f}",
        "ci_high_odds_ratio": f"{math.exp(high):.6f}", "tau_squared_DL": f"{tau:.6f}",
        "Q": f"{q:.6f}", "Q_df": str(df), "I_squared_percent": f"{i2:.3f}",
        "interpretation_boundary": "Methodological audit meta-analysis only; this does not estimate a biological trait effect.",
    }


def build_evidence_yield_meta(
    screened_rows: Iterable[dict[str, str]], audit_rows: Iterable[dict[str, str]]
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, object], dict[str, str]]:
    screened = list(screened_rows)
    audit = validate_audit(audit_rows)
    counts = screen_universe_counts(screened)
    priors = {group: _fit_group_prior(audit, group) for group in VALID_AUDIT_GROUPS}
    lookup = {(row["route_family_audit"], row["audit_group"]): row for row in audit}
    output: list[dict[str, str]] = []
    for ordinal, (route, group) in enumerate(sorted(lookup), start=1):
        row = lookup[(route, group)]
        y = as_int(row["direct_route_present_rows"], "direct_route_present_rows")
        n = as_int(row["route_screenable_rows"], "route_screenable_rows")
        alpha0, beta0 = priors[group]
        samples = beta_samples(alpha0 + y, beta0 + n - y, 20260702 + ordinal)
        rate_low, rate_high = q025_q975(samples)
        l2_n = counts[(route, group)]["l2"]
        abstract_n = counts[(route, group)]["abstract_available"]
        all_projection = [sample * l2_n for sample in samples]
        abstract_projection = [sample * abstract_n for sample in samples]
        all_low, all_high = q025_q975(all_projection)
        abstract_low, abstract_high = q025_q975(abstract_projection)
        output.append({
            "route": route, "audit_group": group,
            "l1_candidate_memberships": str(counts[(route, group)]["l1"]),
            "l2_candidate_memberships": str(l2_n),
            "l2_abstract_available_memberships": str(abstract_n),
            "audit_sampled_rows": row["sampled_rows"], "audit_screenable_rows": row["route_screenable_rows"],
            "audit_direct_route_rows": row["direct_route_present_rows"],
            "audit_direct_route_yield": f"{y / n:.6f}" if n else "",
            "posterior_model": "group_level_empirical_bayes_beta_binomial",
            "posterior_direct_rate_mean": f"{sum(samples) / len(samples):.6f}",
            "posterior_direct_rate_ci_low": f"{rate_low:.6f}",
            "posterior_direct_rate_ci_high": f"{rate_high:.6f}",
            "equal_yield_projection_mean": f"{sum(all_projection) / len(all_projection):.3f}",
            "equal_yield_projection_ci_low": f"{all_low:.3f}",
            "equal_yield_projection_ci_high": f"{all_high:.3f}",
            "abstract_proxy_projection_mean": f"{sum(abstract_projection) / len(abstract_projection):.3f}",
            "abstract_proxy_projection_ci_low": f"{abstract_low:.3f}",
            "abstract_proxy_projection_ci_high": f"{abstract_high:.3f}",
            "projection_boundary": "Projections are calibrated sensitivity estimates, not counts of confirmed empirical studies.",
        })
    route_effects, screening_summary = priority_screen_meta(audit)
    diagnostics: dict[str, object] = {
        "schema_version": "l1_l2_evidence_yield_meta_v1",
        "analysis_target": "direct-route evidence yield, not biological effect magnitude",
        "l1_candidate_count": len(screened),
        "audit_sampled_rows": sum(as_int(row["sampled_rows"], "sampled_rows") for row in audit),
        "audit_screenable_rows": sum(as_int(row["route_screenable_rows"], "route_screenable_rows") for row in audit),
        "audit_unassessed_rows": sum(as_int(row["unassessed_rows"], "unassessed_rows") for row in audit),
        "group_priors": {group: {"alpha": pair[0], "beta": pair[1]} for group, pair in priors.items()},
        "boundary": "Route memberships are discovery strata and may overlap; projected counts are not independent-study totals.",
    }
    return output, route_effects, diagnostics, screening_summary


def write_outputs(out_dir: str | Path, route_rows: Iterable[dict[str, str]], effect_rows: Iterable[dict[str, str]], diagnostics: dict[str, object], summary: dict[str, str]) -> None:
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    for filename, fields, rows in (
        ("evidence_yield_by_route_group.csv", ROUTE_GROUP_FIELDS, route_rows),
        ("priority_screen_route_effects.csv", SCREEN_META_FIELDS, effect_rows),
        ("priority_screen_random_effects_summary.csv", META_SUMMARY_FIELDS, [summary]),
    ):
        with (destination / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    (destination / "evidence_yield_meta_diagnostics.json").write_text(json.dumps(diagnostics, indent=2, sort_keys=True), encoding="utf-8")
