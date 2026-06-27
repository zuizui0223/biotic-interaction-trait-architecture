"""Decision rules for iterative Megachile discovery experiments.

This module does not browse the web. It evaluates reviewed candidate batches and
chooses the next source class or search granularity according to predeclared
yield thresholds. That keeps the exploration adaptive without silently changing
what counts as usable evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class DiscoveryRound:
    strategy_id: str
    candidates_checked: int
    direct_actions: int
    plant_named_any_rank: int
    trait_ready_records: int

    def __post_init__(self) -> None:
        values = (self.candidates_checked, self.direct_actions, self.plant_named_any_rank, self.trait_ready_records)
        if any(value < 0 for value in values):
            raise ValueError("round counts must be non-negative")
        if self.direct_actions > self.candidates_checked:
            raise ValueError("direct_actions cannot exceed candidates_checked")
        if self.plant_named_any_rank > self.direct_actions:
            raise ValueError("plant_named_any_rank cannot exceed direct_actions")
        if self.trait_ready_records > self.plant_named_any_rank:
            raise ValueError("trait_ready_records cannot exceed plant_named_any_rank")

    @property
    def action_yield(self) -> float:
        return self.direct_actions / self.candidates_checked if self.candidates_checked else 0.0

    @property
    def plant_yield(self) -> float:
        return self.plant_named_any_rank / self.direct_actions if self.direct_actions else 0.0

    @property
    def trait_yield(self) -> float:
        return self.trait_ready_records / self.candidates_checked if self.candidates_checked else 0.0


@dataclass(frozen=True)
class AdaptationDecision:
    status: str
    next_strategy_id: str | None
    rationale: str


DEFAULT_STRATEGY_ORDER = (
    "image_observation_genus_action",
    "source_internal_action_search",
    "local_natural_history_archive",
    "literature_citation_chasing",
)


def decide_next_strategy(
    round_: DiscoveryRound,
    *,
    strategy_order: tuple[str, ...] = DEFAULT_STRATEGY_ORDER,
    min_batch_size: int = 20,
    min_action_yield: float = 0.05,
    min_trait_yield: float = 0.02,
) -> AdaptationDecision:
    """Choose whether to expand, refine, or pivot after one reviewed batch.

    The rule is intentionally conservative: a short pilot can reveal that a
    source is unproductive, but cannot establish a source as final evidence.
    """
    if round_.candidates_checked < min_batch_size:
        return AdaptationDecision(
            status="continue_batch",
            next_strategy_id=round_.strategy_id,
            rationale=f"Only {round_.candidates_checked} candidates checked; complete the fixed batch of {min_batch_size} before comparing strategies.",
        )
    if round_.direct_actions == 0:
        return AdaptationDecision(
            status="pivot_source_class",
            next_strategy_id=_next_strategy(round_.strategy_id, strategy_order),
            rationale="No direct material actions in a completed batch; do not expand this source class.",
        )
    if round_.trait_ready_records == 0:
        return AdaptationDecision(
            status="retain_for_action_only_and_pivot_plant_search",
            next_strategy_id=_next_strategy(round_.strategy_id, strategy_order),
            rationale="Direct actions were recovered but no species-level bee–plant records were produced; retain this source only for material-mode classification.",
        )
    if round_.trait_yield >= min_trait_yield:
        return AdaptationDecision(
            status="expand_strategy",
            next_strategy_id=round_.strategy_id,
            rationale=f"Trait-ready yield {round_.trait_yield:.3f} meets the expansion threshold {min_trait_yield:.3f}.",
        )
    if round_.action_yield >= min_action_yield:
        return AdaptationDecision(
            status="refine_within_source",
            next_strategy_id="source_internal_action_search",
            rationale="Direct-action yield is adequate but trait-ready yield is low; search within successful sources for plant labels and original observation context before widening scope.",
        )
    return AdaptationDecision(
        status="pivot_source_class",
        next_strategy_id=_next_strategy(round_.strategy_id, strategy_order),
        rationale="Some action evidence exists, but both action and trait-ready yields are below thresholds.",
    )


def _next_strategy(current: str, order: tuple[str, ...]) -> str | None:
    try:
        index = order.index(current)
    except ValueError:
        return order[0] if order else None
    return order[index + 1] if index + 1 < len(order) else None


def round_from_records(strategy_id: str, records: Iterable[Mapping[str, object]]) -> DiscoveryRound:
    """Summarise reviewed candidate rows from the observation-action schema."""
    rows = list(records)
    direct = [row for row in rows if str(row.get("action_status", "")).strip() == "material_action_confirmed"]
    named = [row for row in direct if str(row.get("plant_taxon_status", "")).strip() not in {"", "not_recorded", "unresolved"}]
    trait_ready = [row for row in direct if str(row.get("plant_taxon_status", "")).strip() in {"accepted", "synonym_resolved"}]
    return DiscoveryRound(
        strategy_id=strategy_id,
        candidates_checked=len(rows),
        direct_actions=len(direct),
        plant_named_any_rank=len(named),
        trait_ready_records=len(trait_ready),
    )
