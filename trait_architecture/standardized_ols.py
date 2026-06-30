"""Small dependency-free OLS implementation for predeclared effect extraction.

The implementation is intentionally narrow: complete-case Gaussian regression
with a Moore-free normal-equation solve and HC3 robust covariance. It is used
only where the model formula, transforms, and covariates are declared before
fitting. It does not select predictors, optimize transformations, or perform
post hoc model search.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import erf, isfinite, sqrt
from typing import Iterable, Sequence


@dataclass(frozen=True)
class OlsCoefficient:
    term: str
    estimate: float
    hc3_se: float
    z_value: float
    p_value_normal: float
    ci95_lower: float
    ci95_upper: float


@dataclass(frozen=True)
class OlsResult:
    n: int
    parameter_count: int
    residual_df: int
    r_squared: float
    coefficients: tuple[OlsCoefficient, ...]


def _identity(size: int) -> list[list[float]]:
    return [[1.0 if i == j else 0.0 for j in range(size)] for i in range(size)]


def _transpose(matrix: Sequence[Sequence[float]]) -> list[list[float]]:
    return [list(column) for column in zip(*matrix)]


def _matmul(left: Sequence[Sequence[float]], right: Sequence[Sequence[float]]) -> list[list[float]]:
    if not left or not right:
        raise ValueError("cannot multiply empty matrices")
    if len(left[0]) != len(right):
        raise ValueError("matrix dimensions do not align")
    return [
        [sum(left[i][k] * right[k][j] for k in range(len(right))) for j in range(len(right[0]))]
        for i in range(len(left))
    ]


def _matvec(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> list[float]:
    if not matrix or len(matrix[0]) != len(vector):
        raise ValueError("matrix/vector dimensions do not align")
    return [sum(row[index] * vector[index] for index in range(len(vector))) for row in matrix]


def _invert(matrix: Sequence[Sequence[float]], *, tolerance: float = 1e-12) -> list[list[float]]:
    """Invert a square non-singular matrix with Gauss-Jordan elimination."""

    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("matrix must be a non-empty square matrix")
    augmented = [list(map(float, row)) + identity_row for row, identity_row in zip(matrix, _identity(size))]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) <= tolerance:
            raise ValueError("design matrix is singular or numerically rank deficient")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor:
                augmented[row] = [
                    augmented[row][index] - factor * augmented[column][index]
                    for index in range(2 * size)
                ]
    return [row[size:] for row in augmented]


def _normal_two_sided_p(z_value: float) -> float:
    return max(0.0, min(1.0, 1.0 - erf(abs(z_value) / sqrt(2.0))))


def fit_ols_hc3(
    y: Iterable[float],
    design: Iterable[Iterable[float]],
    terms: Sequence[str],
) -> OlsResult:
    """Fit OLS with HC3 robust standard errors.

    `design` must include the intercept column and correspond exactly to `terms`.
    The caller is responsible for declared complete-case handling and transforms.
    """

    response = [float(value) for value in y]
    matrix = [list(map(float, row)) for row in design]
    if len(response) != len(matrix) or not response:
        raise ValueError("response and design must contain the same non-zero number of rows")
    if not terms or any(len(row) != len(terms) for row in matrix):
        raise ValueError("every design row must match the supplied terms")
    if any(not isfinite(value) for value in response) or any(
        not isfinite(value) for row in matrix for value in row
    ):
        raise ValueError("response and design must be finite")
    n = len(response)
    parameter_count = len(terms)
    if n <= parameter_count:
        raise ValueError("OLS requires more complete rows than model parameters")

    xt = _transpose(matrix)
    xtx = _matmul(xt, matrix)
    xtx_inverse = _invert(xtx)
    xty = _matvec(xt, response)
    beta = _matvec(xtx_inverse, xty)
    fitted = _matvec(matrix, beta)
    residuals = [observed - predicted for observed, predicted in zip(response, fitted)]
    y_mean = sum(response) / n
    total_sum_squares = sum((value - y_mean) ** 2 for value in response)
    residual_sum_squares = sum(value * value for value in residuals)
    r_squared = 1.0 - residual_sum_squares / total_sum_squares if total_sum_squares > 0 else 0.0

    # HC3 sandwich covariance: (X'X)^-1 [sum x_i x_i' e_i^2/(1-h_ii)^2] (X'X)^-1.
    meat = [[0.0 for _ in range(parameter_count)] for _ in range(parameter_count)]
    for row, residual in zip(matrix, residuals):
        leverage = sum(
            row[left] * xtx_inverse[left][right] * row[right]
            for left in range(parameter_count)
            for right in range(parameter_count)
        )
        denominator = max(1e-12, 1.0 - leverage)
        weight = (residual / denominator) ** 2
        for left in range(parameter_count):
            for right in range(parameter_count):
                meat[left][right] += weight * row[left] * row[right]
    covariance = _matmul(_matmul(xtx_inverse, meat), xtx_inverse)
    coefficients: list[OlsCoefficient] = []
    for index, term in enumerate(terms):
        variance = max(0.0, covariance[index][index])
        se = sqrt(variance)
        z_value = beta[index] / se if se > 0 else float("nan")
        p_value = _normal_two_sided_p(z_value) if isfinite(z_value) else float("nan")
        coefficients.append(OlsCoefficient(
            term=term,
            estimate=beta[index],
            hc3_se=se,
            z_value=z_value,
            p_value_normal=p_value,
            ci95_lower=beta[index] - 1.96 * se,
            ci95_upper=beta[index] + 1.96 * se,
        ))
    return OlsResult(
        n=n,
        parameter_count=parameter_count,
        residual_df=n - parameter_count,
        r_squared=r_squared,
        coefficients=tuple(coefficients),
    )
