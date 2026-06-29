"""Scale-specific synthesis for four-path floral interaction effects.

This module implements a deliberately conservative first synthesis layer. It
performs separate DerSimonian–Laird random-effects summaries for records sharing
all of:

* Part I effect role;
* reported effect scale; and
* causal-status stratum.

It never converts ratios, odds ratios, visitor rates, or standardized slopes
silently. It also refuses to pool more than one nominally independent primary
effect from a study within the same group. A richer multilevel/dependence model
can replace this layer after enough recoverable data accumulate, but it must
retain these scale and study-dependence checks.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping

from .four_path_effects import audit_effect_registry


POOLABLE_EFFECT_MEASURES = frozenset(
    {
        "standardized_regression_slope",
        "log_response_ratio",
        "log_odds_ratio",
        "standardized_mean_difference",
        "fisher_z",
    }
)


@dataclass(frozen=True)
class SynthesisSummary:
    """One study-independent random-effects summary on a common reported scale."""

    effect_role: str
    effect_measure: str
    causal_status: str
    parameter_target: str
    n_effects: int
    n_studies: int
    fixed_effect_estimate: float
    random_effect_estimate: float
    random_effect_se: float
    ci95_lower: float
    ci95_upper: float
    tau2: float
    q: float
    q_df: int
    i2_percent: float
    synthesis_status: str
    notes: str


def _text(value: object) -> str:
    return str(value or "").strip()


def _float(row: Mapping[str, str], field: str) -> float:
    try:
        value = float(_text(row.get(field)))
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be numeric") from error
    if not math.isfinite(value):
        raise ValueError(f"{field} must be finite")
    return value


def _eligible_records(records: Iterable[Mapping[str, str]]) -> tuple[list[dict[str, str]], list[str]]:
    rows = [{key: _text(value) for key, value in row.items()} for row in records]
    audit = audit_effect_registry(rows)
    summary_by_id = {summary.effect_id: summary for summary in audit.summaries}
    eligible: list[dict[str, str]] = []
    warnings: list[str] = list(audit.warnings)
    for row in rows:
        effect_id = _text(row.get("effect_id"))
        summary = summary_by_id.get(effect_id)
        if summary is None or not summary.analysis_ready:
            continue
        if row["effect_measure"] not in POOLABLE_EFFECT_MEASURES:
            warnings.append(
                f"{effect_id}: effect_measure={row['effect_measure']} retained in registry but not pooled without an explicit scale conversion."
            )
            continue
        if not _text(row.get("effect_se")):
            warnings.append(f"{effect_id}: missing SE; no inverse-variance synthesis.")
            continue
        try:
            estimate = _float(row, "effect_estimate")
            se = _float(row, "effect_se")
        except ValueError as error:
            warnings.append(f"{effect_id}: {error}")
            continue
        if se <= 0:
            warnings.append(f"{effect_id}: effect_se must be positive for synthesis.")
            continue
        row["effect_estimate"] = str(estimate)
        row["effect_se"] = str(se)
        eligible.append(row)
    return eligible, warnings


def _parameter_target(effect_role: str) -> str:
    return {
        "A_to_pollination": "b_A",
        "A_to_antagonism": "d_A",
        "B_to_antagonism": "e_F",
        "B_to_pollination": "c_D",
    }.get(effect_role, "not_identified")


def _group_key(row: Mapping[str, str]) -> tuple[str, str, str]:
    return (
        _text(row.get("effect_role")),
        _text(row.get("effect_measure")),
        _text(row.get("causal_status")),
    )


def _check_study_independence(rows: list[dict[str, str]]) -> tuple[bool, str]:
    studies = [row["study_id"] for row in rows]
    duplicates = sorted({study for study in studies if studies.count(study) > 1})
    if duplicates:
        return False, "multiple records from one study require a declared dependence model: " + "; ".join(duplicates)
    return True, ""


def _random_effects_summary(key: tuple[str, str, str], rows: list[dict[str, str]]) -> SynthesisSummary:
    role, measure, causal = key
    independent, note = _check_study_independence(rows)
    if not independent:
        return SynthesisSummary(
            effect_role=role,
            effect_measure=measure,
            causal_status=causal,
            parameter_target=_parameter_target(role),
            n_effects=len(rows),
            n_studies=len({row['study_id'] for row in rows}),
            fixed_effect_estimate=float("nan"),
            random_effect_estimate=float("nan"),
            random_effect_se=float("nan"),
            ci95_lower=float("nan"),
            ci95_upper=float("nan"),
            tau2=float("nan"),
            q=float("nan"),
            q_df=max(0, len(rows) - 1),
            i2_percent=float("nan"),
            synthesis_status="blocked_study_dependence",
            notes=note,
        )

    estimates = [_float(row, "effect_estimate") for row in rows]
    variances = [_float(row, "effect_se") ** 2 for row in rows]
    weights = [1.0 / variance for variance in variances]
    total_weight = sum(weights)
    fixed = sum(weight * estimate for weight, estimate in zip(weights, estimates)) / total_weight
    q = sum(weight * (estimate - fixed) ** 2 for weight, estimate in zip(weights, estimates))
    df = len(rows) - 1
    correction = total_weight - sum(weight * weight for weight in weights) / total_weight
    tau2 = max(0.0, (q - df) / correction) if df > 0 and correction > 0 else 0.0
    random_weights = [1.0 / (variance + tau2) for variance in variances]
    total_random_weight = sum(random_weights)
    random = sum(weight * estimate for weight, estimate in zip(random_weights, estimates)) / total_random_weight
    random_se = math.sqrt(1.0 / total_random_weight)
    i2 = max(0.0, (q - df) / q * 100.0) if q > 0 and df > 0 else 0.0
    return SynthesisSummary(
        effect_role=role,
        effect_measure=measure,
        causal_status=causal,
        parameter_target=_parameter_target(role),
        n_effects=len(rows),
        n_studies=len(rows),
        fixed_effect_estimate=fixed,
        random_effect_estimate=random,
        random_effect_se=random_se,
        ci95_lower=random - 1.96 * random_se,
        ci95_upper=random + 1.96 * random_se,
        tau2=tau2,
        q=q,
        q_df=df,
        i2_percent=i2,
        synthesis_status="summarised" if len(rows) >= 2 else "single_effect_no_between_study_inference",
        notes="DerSimonian–Laird random-effects summary on the reported scale; no cross-scale conversion.",
    )


def synthesise_effect_registry(records: Iterable[Mapping[str, str]]) -> tuple[tuple[SynthesisSummary, ...], tuple[str, ...]]:
    """Summarise eligible registry records in role/scale/design strata."""

    eligible, warnings = _eligible_records(records)
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in eligible:
        grouped.setdefault(_group_key(row), []).append(row)
    summaries = tuple(
        _random_effects_summary(key, rows)
        for key, rows in sorted(grouped.items())
    )
    if not summaries:
        warnings.append("No records are currently eligible for inverse-variance synthesis.")
    return summaries, tuple(warnings)


def synthesis_report_to_dict(
    summaries: Iterable[SynthesisSummary], warnings: Iterable[str] = (),
) -> dict[str, object]:
    return {
        "summaries": [asdict(summary) for summary in summaries],
        "warnings": list(warnings),
        "interpretation": "Every summary remains on its declared effect scale and causal-status stratum. It is not an absolute Part I parameter calibration.",
    }
