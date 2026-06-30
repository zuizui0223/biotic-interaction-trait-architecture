"""Prepare predeclared standardized pathway models for the Impatiens archive.

This module keeps raw observations in memory. It exposes only complete-case
matrices and aggregate diagnostics for the predeclared model specification.
"""

from __future__ import annotations

import math
from statistics import mean, stdev
from typing import Any


MISSING = {"", "na", "nan", "n/a", "null", "none"}


def _text(value: object) -> str:
    return str(value or "").strip()


def _number(value: object, field: str) -> float:
    if _text(value).lower() in MISSING:
        raise ValueError(f"{field} missing")
    result = float(_text(value))
    if not math.isfinite(result):
        raise ValueError(f"{field} not finite")
    return result


def transform(value: float, name: str) -> float:
    if name == "identity_then_zscore":
        return value
    if name == "log1p_then_zscore":
        if value < 0:
            raise ValueError("log1p requires non-negative value")
        return math.log1p(value)
    if name == "log_then_zscore":
        if value <= 0:
            raise ValueError("log requires positive value")
        return math.log(value)
    if name == "arcsine_sqrt_percent_then_zscore":
        if not 0 <= value <= 100:
            raise ValueError("percent must lie in [0,100]")
        return math.asin(math.sqrt(value / 100.0))
    raise ValueError(f"unknown transform: {name}")


def zscore(values: list[float]) -> list[float]:
    if len(values) < 2:
        raise ValueError("z-score needs two observations")
    location, spread = mean(values), stdev(values)
    if spread <= 0:
        raise ValueError("z-score needs a non-constant value")
    return [(value - location) / spread for value in values]


def yn(value: object, field: str) -> float:
    label = _text(value).upper()
    if label == "Y":
        return 1.0
    if label == "N":
        return 0.0
    raise ValueError(f"{field} must be Y/N")


def prepare_rows(
    raw_rows: list[dict[str, str]],
    *,
    outcome_field: str,
    outcome_transform: str,
    attraction_field: str,
    attraction_transform: str,
    barrier_field: str,
    barrier_transform: str,
    phenology_field: str,
) -> tuple[list[dict[str, float]], int]:
    """Return complete cases and count of omitted rows for one predeclared model."""

    kept: list[dict[str, float]] = []
    omitted = 0
    for row in raw_rows:
        try:
            kept.append({
                "y": transform(_number(row.get(outcome_field), outcome_field), outcome_transform),
                "A": transform(_number(row.get(attraction_field), attraction_field), attraction_transform),
                "B": transform(_number(row.get(barrier_field), barrier_field), barrier_transform),
                "Robbing_Y": yn(row.get("Robbing"), "Robbing"),
                "Florivory_Y": yn(row.get("Florivory"), "Florivory"),
                "Pollination_Y": yn(row.get("Pollination"), "Pollination"),
                "Phenology": _number(row.get(phenology_field), phenology_field),
            })
        except (ValueError, TypeError):
            omitted += 1
    return kept, omitted


def design_matrix(rows: list[dict[str, float]], *, interaction: bool) -> tuple[list[float], list[list[float]], list[str]]:
    """Standardize outcome/traits/phenology inside the declared complete-case sample."""

    y = zscore([row["y"] for row in rows])
    a = zscore([row["A"] for row in rows])
    b = zscore([row["B"] for row in rows])
    phenology = zscore([row["Phenology"] for row in rows])
    terms = ["Intercept", "A_z", "B_z"]
    if interaction:
        terms.append("A_z:B_z")
    terms.extend(["Robbing_Y", "Florivory_Y", "Pollination_Y", "Phenology_z"])
    design: list[list[float]] = []
    for index, row in enumerate(rows):
        values = [1.0, a[index], b[index]]
        if interaction:
            values.append(a[index] * b[index])
        values.extend([row["Robbing_Y"], row["Florivory_Y"], row["Pollination_Y"], phenology[index]])
        design.append(values)
    return y, design, terms


def has_interaction(model: dict[str, Any]) -> bool:
    return "A_z:B_z" in str(model.get("model", ""))
