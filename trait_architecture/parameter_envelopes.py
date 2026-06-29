"""Validate the explicit bridge from empirical summaries to Part I envelopes.

The bridge is intentionally not an automatic coefficient conversion.  It checks
whether each parameter has a declared, compatible effect-summary stratum and a
written low/mid/high dimensionless calibration.  Only fully declared contracts
can feed an empirical-envelope robustness run.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping


TARGET_TO_ROLE = {
    "attraction_gain": "A_to_pollination",
    "attraction_tracking": "A_to_antagonism",
    "floral_defence_efficacy": "B_to_antagonism",
    "defence_pollinator_cost": "B_to_pollination",
}
CALIBRATION_STATES = frozenset(
    {
        "awaiting_synthesis",
        "manual_calibration_required",
        "calibrated_envelope",
        "not_parameterizable",
    }
)


@dataclass(frozen=True)
class EnvelopeReadiness:
    contract_id: str
    target_parameter: str
    effect_role: str
    effect_measure: str
    causal_status: str
    calibration_status: str
    matching_summary_found: bool
    ready_for_empirical_sweep: bool
    warnings: tuple[str, ...]


def _text(value: object) -> str:
    return str(value or "").strip()


def _number(value: object, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be numeric") from error
    return number


def load_contracts(path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("parameter-envelope contract file must contain a JSON object")
    contracts = payload.get("contracts")
    if not isinstance(contracts, list):
        raise ValueError("parameter-envelope contract file requires a contracts list")
    return payload


def _summary_key(summary: Mapping[str, object]) -> tuple[str, str, str]:
    return (
        _text(summary.get("effect_role")),
        _text(summary.get("effect_measure")),
        _text(summary.get("causal_status")),
    )


def _check_envelope_values(contract: Mapping[str, object], warnings: list[str]) -> bool:
    values = []
    for field in ("low", "mid", "high"):
        value = contract.get(field)
        if value is None or _text(value) == "":
            warnings.append(f"missing {field} envelope value")
            return False
        try:
            values.append(_number(value, field))
        except ValueError as error:
            warnings.append(str(error))
            return False
    low, mid, high = values
    if not low <= mid <= high:
        warnings.append("envelope values must satisfy low <= mid <= high")
        return False
    target = _text(contract.get("target_parameter"))
    if low < 0:
        warnings.append("Part I parameter envelopes must be non-negative")
        return False
    if target == "floral_defence_efficacy" and high > 1:
        warnings.append("floral_defence_efficacy envelope must lie in [0,1]")
        return False
    return True


def validate_contracts(
    contracts_payload: Mapping[str, object],
    synthesis_summaries: Iterable[Mapping[str, object]],
) -> tuple[EnvelopeReadiness, ...]:
    """Validate every required channel against current scale-specific summaries."""

    raw_contracts = contracts_payload.get("contracts")
    if not isinstance(raw_contracts, list):
        raise ValueError("contracts must be a list")
    summaries = list(synthesis_summaries)
    summary_keys = {
        _summary_key(summary)
        for summary in summaries
        if _text(summary.get("synthesis_status")) in {
            "summarised",
            "single_effect_no_between_study_inference",
        }
    }
    seen_targets: set[str] = set()
    readiness: list[EnvelopeReadiness] = []
    for raw in raw_contracts:
        if not isinstance(raw, Mapping):
            raise ValueError("each calibration contract must be an object")
        warnings: list[str] = []
        contract_id = _text(raw.get("contract_id"))
        target = _text(raw.get("target_parameter"))
        role = _text(raw.get("effect_role"))
        measure = _text(raw.get("effect_measure"))
        causal = _text(raw.get("causal_status"))
        state = _text(raw.get("calibration_status"))
        if not contract_id:
            warnings.append("missing contract_id")
        if target not in TARGET_TO_ROLE:
            warnings.append("target_parameter is not a supported four-path Part I parameter")
        elif target in seen_targets:
            warnings.append("duplicate target_parameter contract")
        else:
            seen_targets.add(target)
        if target in TARGET_TO_ROLE and role != TARGET_TO_ROLE[target]:
            warnings.append("effect_role is incompatible with target_parameter")
        if state not in CALIBRATION_STATES:
            warnings.append("calibration_status is not declared")
        if not _text(raw.get("proxy_justification")) and state == "calibrated_envelope":
            warnings.append("calibrated contract requires proxy_justification")
        if not _text(raw.get("source_selector")) and state == "calibrated_envelope":
            warnings.append("calibrated contract requires source_selector")
        matching = (role, measure, causal) in summary_keys
        if state == "calibrated_envelope":
            _check_envelope_values(raw, warnings)
            if not matching:
                warnings.append("no compatible synthesised effect stratum found")
        ready = state == "calibrated_envelope" and matching and not warnings
        readiness.append(
            EnvelopeReadiness(
                contract_id=contract_id or "<missing contract_id>",
                target_parameter=target or "<missing target_parameter>",
                effect_role=role or "<missing effect_role>",
                effect_measure=measure or "<missing effect_measure>",
                causal_status=causal or "<missing causal_status>",
                calibration_status=state or "<missing calibration_status>",
                matching_summary_found=matching,
                ready_for_empirical_sweep=ready,
                warnings=tuple(warnings),
            )
        )
    missing_targets = sorted(set(TARGET_TO_ROLE).difference(seen_targets))
    for target in missing_targets:
        readiness.append(
            EnvelopeReadiness(
                contract_id="<missing contract>",
                target_parameter=target,
                effect_role=TARGET_TO_ROLE[target],
                effect_measure="",
                causal_status="",
                calibration_status="missing",
                matching_summary_found=False,
                ready_for_empirical_sweep=False,
                warnings=("no calibration contract declared",),
            )
        )
    return tuple(sorted(readiness, key=lambda item: item.target_parameter))


def ready_parameter_overrides(
    contracts_payload: Mapping[str, object],
    readiness: Iterable[EnvelopeReadiness],
) -> dict[str, dict[str, float]]:
    """Return low/mid/high parameter values only when every channel is ready."""

    by_target = {item.target_parameter: item for item in readiness}
    if set(by_target) != set(TARGET_TO_ROLE) or not all(item.ready_for_empirical_sweep for item in by_target.values()):
        raise ValueError("all four channel contracts must be calibrated before building an empirical envelope")
    raw_by_target = {
        _text(contract.get("target_parameter")): contract
        for contract in contracts_payload.get("contracts", [])
        if isinstance(contract, Mapping)
    }
    return {
        level: {
            target: _number(raw_by_target[target][level], f"{target}.{level}")
            for target in TARGET_TO_ROLE
        }
        for level in ("low", "mid", "high")
    }


def readiness_report_to_dict(readiness: Iterable[EnvelopeReadiness]) -> dict[str, object]:
    records = list(readiness)
    return {
        "contracts": [asdict(record) for record in records],
        "all_channels_ready": bool(records) and all(record.ready_for_empirical_sweep for record in records),
        "interpretation": "No empirical parameter envelope is created until every channel has a compatible scale-specific summary and an explicit calibration contract.",
    }
