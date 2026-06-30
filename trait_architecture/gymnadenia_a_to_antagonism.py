"""Predeclared observational A→floral-antagonism extraction for *Gymnadenia*.

The public Dryad archive is read in memory. Outputs contain only aggregate
analysis counts and one fitted coefficient; individual observations, identifiers,
and raw values are never written.
"""

from __future__ import annotations

import json
import math
import zipfile
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import Any, Callable

from trait_architecture.dalechampia_linked_panel import _dataset_chain, _fetch_bytes, _fetch_json, _normalise_doi
from trait_architecture.gymnadenia_row_linkage import KEY_CANDIDATES, _read_target_tables


TRAIT_COLUMN = "TotalScentAmount_ngPerL"
FLOWER_COLUMN = "NrFlowers"
EATEN_COLUMN = "NrFlowersEaten"
MAX_ITERATIONS = 100
CONVERGENCE_TOLERANCE = 1e-9


def _number(value: object) -> float | None:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _integer_count(value: object) -> int | None:
    number = _number(value)
    if number is None or number < 0 or abs(number - round(number)) > 1e-8:
        return None
    return int(round(number))


def _key(record: dict[str, str], columns: tuple[str, ...] = KEY_CANDIDATES) -> tuple[str, ...] | None:
    values = tuple(record.get(column, "").strip() for column in columns)
    return values if all(values) else None


def _unique_records(records: list[dict[str, str]]) -> dict[tuple[str, ...], dict[str, str]]:
    counts: Counter[tuple[str, ...]] = Counter()
    values: dict[tuple[str, ...], dict[str, str]] = {}
    for record in records:
        key = _key(record)
        if key is None:
            continue
        counts[key] += 1
        values[key] = record
    return {key: values[key] for key, count in counts.items() if count == 1}


def _logistic(value: float) -> float:
    if value >= 35:
        return 1.0 - 1e-15
    if value <= -35:
        return 1e-15
    return 1.0 / (1.0 + math.exp(-value))


def _solve_linear(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Solve a square linear system with partial pivoting."""

    n = len(vector)
    augmented = [row[:] + [vector[index]] for index, row in enumerate(matrix)]
    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("singular information matrix")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        for index in range(column, n + 1):
            augmented[column][index] /= scale
        for row in range(n):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor == 0:
                continue
            for index in range(column, n + 1):
                augmented[row][index] -= factor * augmented[column][index]
    return [augmented[row][n] for row in range(n)]


def _inverse(matrix: list[list[float]]) -> list[list[float]]:
    """Invert a square matrix with Gauss-Jordan elimination."""

    n = len(matrix)
    augmented = [
        matrix[row][:] + [1.0 if row == column else 0.0 for column in range(n)]
        for row in range(n)
    ]
    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("singular information matrix")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        for index in range(2 * n):
            augmented[column][index] /= scale
        for row in range(n):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor == 0:
                continue
            for index in range(2 * n):
                augmented[row][index] -= factor * augmented[column][index]
    return [row[n:] for row in augmented]


def _weighted_cross_products(
    design: list[list[float]],
    weights: list[float],
    target: list[float],
) -> tuple[list[list[float]], list[float]]:
    p = len(design[0])
    matrix = [[0.0 for _ in range(p)] for _ in range(p)]
    vector = [0.0 for _ in range(p)]
    for row, weight, value in zip(design, weights, target):
        for left in range(p):
            vector[left] += weight * row[left] * value
            for right in range(left, p):
                matrix[left][right] += weight * row[left] * row[right]
    for left in range(p):
        for right in range(left):
            matrix[left][right] = matrix[right][left]
    return matrix, vector


def _fit_quasi_binomial_logit(
    design: list[list[float]],
    successes: list[int],
    trials: list[int],
) -> dict[str, object]:
    """Fit a binomial-logit model and use conservative quasi-binomial SEs."""

    if not design or len(design) != len(successes) or len(design) != len(trials):
        raise ValueError("design, successes, and trials must have equal nonzero length")
    n = len(design)
    p = len(design[0])
    if n <= p:
        raise ValueError("insufficient rows for fitted parameters")
    beta = [0.0] * p
    converged = False

    for iteration in range(1, MAX_ITERATIONS + 1):
        eta = [sum(value * coefficient for value, coefficient in zip(row, beta)) for row in design]
        probabilities = [_logistic(value) for value in eta]
        weights = [trial * probability * (1.0 - probability) for trial, probability in zip(trials, probabilities)]
        working = [
            value + ((success / trial) - probability) / (probability * (1.0 - probability))
            for value, success, trial, probability in zip(eta, successes, trials, probabilities)
        ]
        information, score = _weighted_cross_products(design, weights, working)
        updated = _solve_linear(information, score)
        delta = max(abs(new - old) for new, old in zip(updated, beta))
        beta = updated
        if delta < CONVERGENCE_TOLERANCE:
            converged = True
            break

    if not converged:
        raise ValueError("binomial-logit model did not converge")

    eta = [sum(value * coefficient for value, coefficient in zip(row, beta)) for row in design]
    probabilities = [_logistic(value) for value in eta]
    weights = [trial * probability * (1.0 - probability) for trial, probability in zip(trials, probabilities)]
    information, _ = _weighted_cross_products(design, weights, [0.0] * n)
    covariance = _inverse(information)
    pearson = sum(
        ((success - trial * probability) ** 2) / max(trial * probability * (1.0 - probability), 1e-15)
        for success, trial, probability in zip(successes, trials, probabilities)
    )
    raw_dispersion = pearson / (n - p)
    conservative_dispersion = max(1.0, raw_dispersion)
    return {
        "coefficients": beta,
        "covariance": covariance,
        "iterations": iteration,
        "converged": converged,
        "pearson_dispersion": raw_dispersion,
        "conservative_dispersion": conservative_dispersion,
        "n": n,
        "p": p,
    }


def _normal_two_sided_p(value: float) -> float:
    return math.erfc(abs(value) / math.sqrt(2.0))


def extract_gymnadenia_a_to_antagonism(
    *,
    dataset_doi: str,
    fetch_json: Callable[[str], tuple[int, Any]] = _fetch_json,
    fetch_bytes: Callable[[str], bytes] = _fetch_bytes,
) -> dict[str, object]:
    """Fit the one predeclared observational total-scent effect.

    Returns only aggregate sample/stratum counts and effect-estimate metadata.
    """

    dataset_doi = _normalise_doi(dataset_doi)
    file_names, version_url, archive_url = _dataset_chain(dataset_doi, fetch_json)
    archive = zipfile.ZipFile(BytesIO(fetch_bytes(archive_url)))
    tables = _read_target_tables(archive)
    floral = tables["floral_traits"]
    herbivory = tables["herbivory"]
    if floral["status"] != "read" or herbivory["status"] != "read":
        raise ValueError("required floral-trait or herbivory table is unavailable")
    if TRAIT_COLUMN not in floral["headers"] or FLOWER_COLUMN not in floral["headers"] or EATEN_COLUMN not in herbivory["headers"]:
        raise ValueError("required total-scent, flower-count, or eaten-flower column is unavailable")

    floral_records = _unique_records(floral["records"])
    herbivory_records = _unique_records(herbivory["records"])
    common_keys = sorted(set(floral_records).intersection(herbivory_records))
    included: list[tuple[float, int, int, tuple[str, ...]]] = []
    excluded: Counter[str] = Counter()
    for key in common_keys:
        trait = _number(floral_records[key].get(TRAIT_COLUMN, ""))
        flowers = _integer_count(floral_records[key].get(FLOWER_COLUMN, ""))
        eaten = _integer_count(herbivory_records[key].get(EATEN_COLUMN, ""))
        if trait is None or trait < 0:
            excluded["invalid_total_scent"] += 1
            continue
        if flowers is None or flowers <= 0:
            excluded["invalid_flower_denominator"] += 1
            continue
        if eaten is None or eaten > flowers:
            excluded["invalid_eaten_flower_outcome"] += 1
            continue
        included.append((math.log1p(trait), eaten, flowers, key))

    if len(included) < 10:
        raise ValueError("fewer than ten valid linked observations")
    scent_values = [row[0] for row in included]
    mean_scent = sum(scent_values) / len(scent_values)
    variance = sum((value - mean_scent) ** 2 for value in scent_values) / (len(scent_values) - 1)
    scent_sd = math.sqrt(variance)
    if scent_sd <= 0:
        raise ValueError("total floral scent has zero variance after transform")

    groups = ["|".join((key[2], key[3], key[1])) for _, _, _, key in included]
    group_counts = Counter(groups)
    categories = sorted(group_counts)
    if len(categories) < 2:
        raise ValueError("fewer than two population-year strata")
    baseline = categories[0]
    dummy_categories = categories[1:]
    design: list[list[float]] = []
    successes: list[int] = []
    trials: list[int] = []
    for log_scent, eaten, flowers, key in included:
        group = "|".join((key[2], key[3], key[1]))
        standardized = (log_scent - mean_scent) / scent_sd
        design.append([1.0, standardized] + [1.0 if group == category else 0.0 for category in dummy_categories])
        successes.append(eaten)
        trials.append(flowers)

    fitted = _fit_quasi_binomial_logit(design, successes, trials)
    beta = fitted["coefficients"][1]
    variance_beta = fitted["covariance"][1][1] * fitted["conservative_dispersion"]
    standard_error = math.sqrt(max(variance_beta, 0.0))
    z_value = beta / standard_error if standard_error > 0 else math.nan
    return {
        "dataset_doi": dataset_doi,
        "version_url": version_url,
        "archive_url": archive_url,
        "manifest_file_count": len(file_names),
        "analysis": {
            "trait_id": "total_floral_scent_amount",
            "trait_column": TRAIT_COLUMN,
            "trait_scaling": "log1p_then_zscore_within_complete_linked_sample",
            "outcome_id": "eaten_flowers_per_total_flowers",
            "outcome_numerator": EATEN_COLUMN,
            "outcome_denominator": FLOWER_COLUMN,
            "model_family": "binomial_logit_quasi_binomial_se",
            "adjustment_set": "population_x_year_fixed_intercepts",
            "grouping_order": "Region|Population|Year",
            "baseline_population_year_stratum": baseline,
        },
        "sample": {
            "candidate_unique_linked_rows": len(common_keys),
            "included_rows": len(included),
            "excluded_counts": dict(sorted(excluded.items())),
            "population_year_strata": len(categories),
            "minimum_stratum_size": min(group_counts.values()),
            "maximum_stratum_size": max(group_counts.values()),
        },
        "effect": {
            "effect_measure": "log_odds_ratio",
            "effect_estimate": beta,
            "effect_se": standard_error,
            "effect_ci_lower": beta - 1.959963984540054 * standard_error,
            "effect_ci_upper": beta + 1.959963984540054 * standard_error,
            "effect_p_value": _normal_two_sided_p(z_value),
            "pearson_dispersion": fitted["pearson_dispersion"],
            "conservative_dispersion": fitted["conservative_dispersion"],
            "fit_iterations": fitted["iterations"],
            "fit_converged": fitted["converged"],
        },
        "decision_boundary": "This is one predeclared conditional observational association. It does not establish a causal scent effect, floral defence, individual pollination, a B_flower path, or D1/D2/D3 status. No observation rows, identifiers, or raw values are emitted.",
    }


def write_gymnadenia_a_to_antagonism_report(out_dir: str | Path, report: dict[str, object]) -> None:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "gymnadenia_a_to_antagonism_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
