"""Robustness evaluator for the Part I floral attraction–barrier score.

The baseline model in :mod:`trait_architecture.model` is intentionally
qualitative. This module does not calibrate it from data. Instead, it evaluates
whether the *sign* of the local A×D mixed partial remains stable when three
biologically motivated nonlinearities are varied:

* saturation of pollination benefit from attraction;
* saturation of defence efficacy against floral antagonists; and
* curvature in the shared attraction–defence allocation cost.

The outputs are regime-map diagnostics. They must not be interpreted as observed
trait covariance or direct evidence of adaptation.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import exp
from typing import Iterable, Sequence

from .model import ModelParameters


@dataclass(frozen=True)
class FunctionalForm:
    """Curvature choices that preserve the biological interpretation of Part I.

    ``attraction_saturation`` is ``q_A`` in
    ``b_A A / (1 + q_A A)``.  ``defence_half_saturation`` is ``h_D`` in
    ``e_F D / (h_D + D)``.  A value of ``None`` retains the baseline linear
    defence effect. ``shared_cost_curvature`` is ``k_AD`` in
    ``c_AD A D [1 + k_AD(A + D)]``.
    """

    form_id: str
    attraction_saturation: float = 0.0
    defence_half_saturation: float | None = None
    shared_cost_curvature: float = 0.0

    def __post_init__(self) -> None:
        if not self.form_id.strip():
            raise ValueError("form_id must be non-empty")
        if self.attraction_saturation < 0:
            raise ValueError("attraction_saturation must be non-negative")
        if self.defence_half_saturation is not None and self.defence_half_saturation <= 0:
            raise ValueError("defence_half_saturation must be positive when provided")
        if self.shared_cost_curvature < 0:
            raise ValueError("shared_cost_curvature must be non-negative")


@dataclass(frozen=True)
class RobustnessCase:
    """One local phenotype and interaction regime used in a sign sweep."""

    case_id: str
    attraction: float
    defence: float
    assurance: float
    pollinator_service: float
    floral_damage_pressure: float

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must be non-empty")
        for name, value in (
            ("attraction", self.attraction),
            ("defence", self.defence),
            ("assurance", self.assurance),
            ("pollinator_service", self.pollinator_service),
            ("floral_damage_pressure", self.floral_damage_pressure),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")


@dataclass(frozen=True)
class MixedPartialResult:
    """Mixed-partial decomposition for one case and functional form."""

    case_id: str
    form_id: str
    antagonism_term: float
    pollination_obstruction_term: float
    shared_cost_term: float
    mixed_partial: float
    sign: str


@dataclass(frozen=True)
class RobustnessSummary:
    """Sign stability across functional forms for one local regime case."""

    case_id: str
    modal_sign: str
    non_neutral_form_count: int
    total_form_count: int
    modal_sign_agreement: float
    robustness_class: str


BASELINE_FORM = FunctionalForm(form_id="baseline")


def default_functional_forms() -> tuple[FunctionalForm, ...]:
    """Return a compact, predeclared family of baseline and nonlinear variants."""

    return (
        BASELINE_FORM,
        FunctionalForm(form_id="saturating_attraction", attraction_saturation=1.0),
        FunctionalForm(form_id="saturating_defence", defence_half_saturation=0.35),
        FunctionalForm(
            form_id="saturating_both_curved_cost",
            attraction_saturation=1.0,
            defence_half_saturation=0.35,
            shared_cost_curvature=1.0,
        ),
    )


def _sign(value: float, tolerance: float) -> str:
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    if value > tolerance:
        return "complementary"
    if value < -tolerance:
        return "substitutable"
    return "neutral"


def _attraction_marginal_gain(parameters: ModelParameters, attraction: float, form: FunctionalForm) -> float:
    """Return d/dA of the chosen pollination attraction-benefit function."""

    denominator = 1.0 + form.attraction_saturation * attraction
    return parameters.attraction_gain / (denominator * denominator)


def _defence_marginal_efficacy(parameters: ModelParameters, defence: float, form: FunctionalForm) -> float:
    """Return d/dD of the chosen protection function, bounded by model efficacy."""

    if form.defence_half_saturation is None:
        return parameters.floral_defence_efficacy
    half = form.defence_half_saturation
    return parameters.floral_defence_efficacy * half / ((half + defence) * (half + defence))


def mixed_partial(
    case: RobustnessCase,
    parameters: ModelParameters,
    form: FunctionalForm = BASELINE_FORM,
    *,
    tolerance: float = 1e-12,
) -> MixedPartialResult:
    """Evaluate the local A×D mixed partial under one functional-form family.

    The decomposition is retained explicitly because empirical effect-size
    synthesis can inform the first two terms but not the allocation-cost term
    without independent cost evidence.
    """

    attraction_gain = _attraction_marginal_gain(parameters, case.attraction, form)
    defence_efficacy = _defence_marginal_efficacy(parameters, case.defence, form)
    antagonism_term = (
        case.floral_damage_pressure
        * parameters.attraction_tracking
        * defence_efficacy
    )
    pollination_obstruction_term = (
        case.pollinator_service
        * attraction_gain
        * parameters.defence_pollinator_cost
        * exp(-parameters.defence_pollinator_cost * case.defence)
        * (1.0 - parameters.assurance_outcross_dilution * case.assurance)
    )
    shared_cost_term = parameters.attraction_defence_shared_cost * (
        1.0 + 2.0 * form.shared_cost_curvature * (case.attraction + case.defence)
    )
    value = antagonism_term - pollination_obstruction_term - shared_cost_term
    return MixedPartialResult(
        case_id=case.case_id,
        form_id=form.form_id,
        antagonism_term=antagonism_term,
        pollination_obstruction_term=pollination_obstruction_term,
        shared_cost_term=shared_cost_term,
        mixed_partial=value,
        sign=_sign(value, tolerance),
    )


def evaluate_forms(
    case: RobustnessCase,
    parameters: ModelParameters,
    forms: Iterable[FunctionalForm] | None = None,
    *,
    tolerance: float = 1e-12,
) -> tuple[MixedPartialResult, ...]:
    """Evaluate a fixed set of response-function families for one regime case."""

    chosen_forms = tuple(forms) if forms is not None else default_functional_forms()
    if not chosen_forms:
        raise ValueError("at least one functional form is required")
    return tuple(mixed_partial(case, parameters, form, tolerance=tolerance) for form in chosen_forms)


def summarise_case(results: Sequence[MixedPartialResult]) -> RobustnessSummary:
    """Classify whether one case retains a sign across all chosen forms."""

    if not results:
        raise ValueError("cannot summarise an empty result set")
    case_ids = {result.case_id for result in results}
    if len(case_ids) != 1:
        raise ValueError("all results must belong to the same case")
    non_neutral = [result.sign for result in results if result.sign != "neutral"]
    total = len(results)
    if not non_neutral:
        return RobustnessSummary(
            case_id=results[0].case_id,
            modal_sign="neutral",
            non_neutral_form_count=0,
            total_form_count=total,
            modal_sign_agreement=0.0,
            robustness_class="mixed_or_sensitive",
        )
    complementary = non_neutral.count("complementary")
    substitutable = non_neutral.count("substitutable")
    modal_sign = "complementary" if complementary >= substitutable else "substitutable"
    agreement = max(complementary, substitutable) / len(non_neutral)
    has_neutral = len(non_neutral) != total
    if agreement == 1.0 and not has_neutral:
        robustness = "structurally_robust"
    elif agreement >= 0.80:
        robustness = "conditional_majority"
    else:
        robustness = "mixed_or_sensitive"
    return RobustnessSummary(
        case_id=results[0].case_id,
        modal_sign=modal_sign,
        non_neutral_form_count=len(non_neutral),
        total_form_count=total,
        modal_sign_agreement=agreement,
        robustness_class=robustness,
    )


def cartesian_cases(
    *,
    attraction: Iterable[float],
    defence: Iterable[float],
    assurance: Iterable[float],
    pollinator_service: Iterable[float],
    floral_damage_pressure: Iterable[float],
) -> tuple[RobustnessCase, ...]:
    """Build deterministic local cases from a declared parameter grid."""

    cases: list[RobustnessCase] = []
    for index, values in enumerate(
        product(attraction, defence, assurance, pollinator_service, floral_damage_pressure),
        start=1,
    ):
        a, d, r, p, h = values
        cases.append(
            RobustnessCase(
                case_id=f"case_{index:04d}",
                attraction=float(a),
                defence=float(d),
                assurance=float(r),
                pollinator_service=float(p),
                floral_damage_pressure=float(h),
            )
        )
    return tuple(cases)
