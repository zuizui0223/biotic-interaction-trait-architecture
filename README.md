# Biotic Interaction Trait Architecture

A theory-to-data research program on how floral attraction and floral barriers
are shaped by mutualist and antagonist regimes.

## Core question

For floral attraction/access \(A\) and floral barrier/resistance \(D\), when do
biotic interactions favour complementarity, substitutability, or neutrality?

The target is a conditional regime map, not a universal trait trade-off:

\[
\mathcal I \longmapsto \mathbf z^*.
\]

## Research architecture

```text
Part I   exact score condition → functional-form robustness map
Part II  reproducible public-data feasibility decisions
Part III four path-specific effect synthesis → parameter envelopes → empirical regime map
```

### Part I: robustness before calibration

The baseline score is qualitative. Before empirical effects are used to constrain
it, the local mixed partial is tested across:

```text
linear versus saturating attraction benefit
linear versus saturating floral defence efficacy
linear versus escalating shared A×D cost
low / baseline / high channel-strength scenarios
local grids of A, D, R, pollinator service P, and floral damage pressure H
```

Each point is labelled:

```text
structurally_robust
conditional_majority
mixed_or_sensitive
```

Key files:

```text
docs/PART_I_ROBUSTNESS_PROTOCOL.md
configs/part_i_robustness_grid.json
trait_architecture/robustness.py
scripts/run_part_i_robustness.py
```

### Part II: do not force a global join

The initial global routes are not the active empirical backbone:

```text
Web of Life × BIEN leaf traits  → insufficient reproducible trait coverage
GloBI antagonist claims         → no sampled-network/effort contract
TRY custom export               → not an active reproducible dependency
```

These are feasibility findings, not negative evidence against Part I.

### Part III-A: direct matched-study cases

A direct case concerns local fitness curvature, not raw trait covariance. The
four directional paths are:

```text
A_flower → pollination            b_A
A_flower → floral antagonism      d_A
B_flower → floral antagonism      e_F
B_flower → pollination            c_D
```

```text
M0  discovery candidate
M1  one-channel or unaligned evidence
M2  aligned two-channel panel with missing paths
D1  four-arrow channel-mechanism panel
D2  D1 plus linked reproductive-fitness surface
D3  D2 plus independently measured/calibrated shared A×B cost
```

Key files:

```text
empirical/matched_flower_regime/MATCHED_STUDY_PROTOCOL.md
docs/theory_empirical_identifiability_reassessment.md
trait_architecture/matched_regime_registry.py
```

### Part III-B: broad four-path effect synthesis

Ideal D2/D3 cases may be rare. The broad route therefore records one
`study × trait × outcome × model effect` at a time, retaining scale and design
rather than forcing all studies into one pooled value.

```text
A_to_pollination
A_to_antagonism
B_to_antagonism
B_to_pollination
```

Role-specific effect distributions later constrain parameter envelopes for the
Part I robustness sweep. Raw coefficients are never inserted directly into the
fitness score, and shared cost \(c_{AD}\) remains a sensitivity parameter until
allocation/cost evidence exists.

Key files:

```text
empirical/four_path_effects/FOUR_PATH_EFFECT_PROTOCOL.md
empirical/four_path_effects/four_path_effect_registry.csv
trait_architecture/four_path_effects.py
examples/audit_four_path_effects.py
```

## Interpretation boundary

Interaction records are not fitness effects, and trait associations are not
automatically selection, defence efficacy, or adaptation. D1 identifies channel
paths; D2/D3 can be reported only as:

```text
compatible_with_declared_scenario
contradicts_declared_scenario
not_identified
```

The project distinguishes floral modules from leaf resource quality and leaf
resistance. Leaf traits or leaf antagonism do not enter the floral A×D result
without an explicit cross-organ bridge.
