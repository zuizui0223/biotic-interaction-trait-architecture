from trait_architecture.model import Architecture, InteractionRegime, ModelParameters, fitness
from trait_architecture.regime_map import classify_strategy, optimise_architecture, sweep_regimes


def test_defence_reduces_damage_when_other_values_are_fixed() -> None:
    regime = InteractionRegime(0.7, 0.8, 0.9)
    no_defence = fitness(Architecture(0.5, 0.0, 0.3), regime)
    defended = fitness(Architecture(0.5, 1.0, 0.3), regime)
    assert defended.floral_damage_loss < no_defence.floral_damage_loss
    assert defended.leaf_damage_loss < no_defence.leaf_damage_loss


def test_defence_can_reduce_pollination_access() -> None:
    regime = InteractionRegime(1.0, 0.0, 0.0)
    parameters = ModelParameters(defence_pollinator_cost=1.0)
    open_flower = fitness(Architecture(1.0, 0.0, 0.0), regime, parameters)
    defended_flower = fitness(Architecture(1.0, 1.0, 0.0), regime, parameters)
    assert defended_flower.outcross_benefit < open_flower.outcross_benefit


def test_assurance_has_more_value_when_pollinator_service_is_low() -> None:
    architecture = Architecture(0.3, 0.2, 1.0)
    high_service = fitness(architecture, InteractionRegime(1.0, 0.0, 0.0))
    low_service = fitness(architecture, InteractionRegime(0.0, 0.0, 0.0))
    assert low_service.assurance_benefit > high_service.assurance_benefit


def test_leaf_pressure_promotes_more_defence_in_baseline_grid() -> None:
    low_leaf = optimise_architecture(InteractionRegime(0.7, 0.0, 0.0), resolution=11)
    high_leaf = optimise_architecture(InteractionRegime(0.7, 0.0, 1.0), resolution=11)
    assert high_leaf.architecture.defence >= low_leaf.architecture.defence


def test_strategy_labels_cover_guarded_and_open_states() -> None:
    assert classify_strategy(Architecture(1.0, 1.0, 1.0)) == "guarded_attraction"
    assert classify_strategy(Architecture(1.0, 0.0, 0.0)) == "open_attraction"


def test_regime_sweep_has_one_solution_per_grid_point() -> None:
    output = sweep_regimes((0.0, 1.0), (0.0, 1.0), (0.0, 1.0), resolution=5)
    assert len(output) == 8
    assert {row.regime.pollinator_service for row in output} == {0.0, 1.0}
