import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "run_part_i_robustness.py"
SPEC = importlib.util.spec_from_file_location("part_i_robustness_runner", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def minimal_config() -> dict:
    return {
        "neutral_tolerance": 1e-12,
        "phenotype_and_regime_grid": {
            "attraction": [0.5],
            "defence": [0.5],
            "assurance": [0.0],
            "pollinator_service": [0.5],
            "floral_damage_pressure": [0.5],
        },
        "parameter_scenarios": [
            {"scenario_id": "baseline", "overrides": {}},
            {"scenario_id": "high_damage", "overrides": {"attraction_tracking": 2.0}},
        ],
        "functional_forms": [
            {
                "form_id": "baseline",
                "attraction_saturation": 0.0,
                "defence_half_saturation": None,
                "shared_cost_curvature": 0.0,
            },
            {
                "form_id": "saturated",
                "attraction_saturation": 1.0,
                "defence_half_saturation": 0.35,
                "shared_cost_curvature": 1.0,
            },
        ],
    }


def test_run_emits_case_form_and_parameter_envelope_summaries() -> None:
    rows, form_summaries, envelope_summaries = MODULE.run(minimal_config())

    assert len(rows) == 4
    assert len(form_summaries) == 2
    assert len(envelope_summaries) == 1
    assert envelope_summaries[0]["total_evaluation_count"] == 4
    assert envelope_summaries[0]["parameter_scenario_count"] == 2
    assert {row["parameter_scenario_id"] for row in rows} == {"baseline", "high_damage"}
    assert {row["parameter_scenario_id"] for row in form_summaries} == {"baseline", "high_damage"}
    assert {row["form_id"] for row in rows} == {"baseline", "saturated"}


def test_rejects_unknown_model_parameter_override() -> None:
    config = minimal_config()
    config["parameter_scenarios"][0]["overrides"] = {"not_a_parameter": 1.0}

    try:
        MODULE.run(config)
    except ValueError as error:
        assert "unknown ModelParameters field" in str(error)
    else:
        raise AssertionError("unknown model parameter should fail validation")
