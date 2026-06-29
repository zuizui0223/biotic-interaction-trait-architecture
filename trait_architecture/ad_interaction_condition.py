"""Exact local attraction--defence interaction condition for the regime model.

This module derives the mixed second derivative of the implemented qualitative
fitness score with respect to attraction ``A`` and defence ``D``.  It is an exact
statement for :func:`trait_architecture.model.fitness`, not a claim about an
empirical covariance, selection gradient, or natural-system effect size.

A positive mixed partial means that, locally in the declared score, increasing
one investment raises the marginal score of the other (complementarity).  A
negative value means local substitutability.  This is distinct from the sign of
covariance among grid optima, which remains a simulation outcome.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import exp

from .model import Architecture, InteractionRegime, ModelParameters


class ADLocalRelation(str, Enum):
    """Local relation between attraction and defence in the implemented score."""

    COMPLEMENTARY = "complementary"
    SUBSTITUTABLE = "substitutable"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class ADInteractionCondition:
    """Decomposition of the exact mixed partial ``d²W / dA dD``.

    ``pollination_access_penalty`` and ``shared_budget_penalty`` enter with a
    negative sign.  ``floral_damage_relief`` enters with a positive sign.
    Leaf-consumer pressure is absent from this direct cross-partial because the
    current model gives leaf defence benefits without an ``A`` interaction.
    """

    pollination_access_penalty: float
    floral_damage_relief: float
    shared_budget_penalty: float
    cross_partial: float
    relation: ADLocalRelation


def attraction_defence_cross_partial(
    architecture: Architecture,
    regime: InteractionRegime,
    parameters: ModelParameters = ModelParameters(),
) -> ADInteractionCondition:
    """Return the exact local attraction--defence mixed partial.

    For the implemented score,

    ``d²W/dA dD = H * tracking * floral_defence_efficacy
                  - P * attraction_gain * defence_pollinator_cost
                    * exp(-defence_pollinator_cost * D)
                    * (1 - assurance_outcross_dilution * R)
                  - attraction_defence_shared_cost``.

    The expression is independent of leaf-consumer pressure ``L`` *directly*.
    ``L`` can still change the optimal level of defence and therefore change the
    simulated covariance across regime optima.
    """

    d = architecture.defence
    r = architecture.assurance
    p = regime.pollinator_service
    h = regime.floral_damage_pressure

    pollination_access_penalty = (
        p
        * parameters.attraction_gain
        * parameters.defence_pollinator_cost
        * exp(-parameters.defence_pollinator_cost * d)
        * (1.0 - parameters.assurance_outcross_dilution * r)
    )
    floral_damage_relief = h * parameters.attraction_tracking * parameters.floral_defence_efficacy
    shared_budget_penalty = parameters.attraction_defence_shared_cost
    cross_partial = floral_damage_relief - pollination_access_penalty - shared_budget_penalty

    if cross_partial > 0.0:
        relation = ADLocalRelation.COMPLEMENTARY
    elif cross_partial < 0.0:
        relation = ADLocalRelation.SUBSTITUTABLE
    else:
        relation = ADLocalRelation.NEUTRAL

    return ADInteractionCondition(
        pollination_access_penalty=pollination_access_penalty,
        floral_damage_relief=floral_damage_relief,
        shared_budget_penalty=shared_budget_penalty,
        cross_partial=cross_partial,
        relation=relation,
    )


def floral_pressure_threshold_for_complementarity(
    architecture: Architecture,
    regime: InteractionRegime,
    parameters: ModelParameters = ModelParameters(),
) -> float | None:
    """Return the strict ``H`` threshold above which the local relation is positive.

    The threshold is defined only when floral antagonists track attraction and
    floral defence has positive efficacy.  A value above one is mathematically
    valid but unreachable on the current unit-interval regime scale.
    """

    denominator = parameters.attraction_tracking * parameters.floral_defence_efficacy
    if denominator <= 0.0:
        return None

    d = architecture.defence
    r = architecture.assurance
    p = regime.pollinator_service
    numerator = (
        p
        * parameters.attraction_gain
        * parameters.defence_pollinator_cost
        * exp(-parameters.defence_pollinator_cost * d)
        * (1.0 - parameters.assurance_outcross_dilution * r)
        + parameters.attraction_defence_shared_cost
    )
    return numerator / denominator
