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
Part II  broad real-world evidence corpus → support / contradiction / gap map
Part III strict four-path records → high-quality quantitative anchors only
Part IV  self-contained field panels → direct D1/D2 tests where public literature is incomplete
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

Part I is the primary inferential engine. It must remain mathematically robust
when broad empirical evidence is sparse, heterogeneous, or contradictory.

Key files:

```text
docs/PART_I_ROBUSTNESS_PROTOCOL.md
configs/part_i_robustness_grid.json
trait_architecture/robustness.py
scripts/run_part_i_robustness.py
```

### Part II: broad real-world evidence

The broad empirical route is deliberately high-recall. It does not require every
paper to measure all four paths on the same biological unit.

```text
A_to_pollination  -> attraction/display traits with pollination outcomes
A_to_antagonism   -> attraction/display traits with floral antagonism outcomes
B_to_antagonism   -> flower-specific resistance/access traits with floral antagonism
B_to_pollination  -> flower-specific resistance/access traits with pollination
joint_channels    -> pollination and floral antagonism jointly considered
```

It asks whether published systems provide directional support, contradiction, or
silence for conditional Part I predictions. Because the fixed corpus collapses
from ~17,900 discovery candidates to a handful of source-adjudicated anchors and
zero currently poolable effect sizes, the two **primary products** are a
source-adjudicated direction map (sign compatibility per channel) and a
yield meta-analysis (how resolvable the evidence base is). A pooled effect-size
synthesis is a **deferred layer**, gated on primary-source recovery of the Layer 4
exact-stratum anchors, not the headline result.

A study can be useful broad evidence even when it is not eligible for direct
four-path calibration. Query membership and title/abstract signals are never
mistaken for measured effects.

Key files:

```text
empirical/broad_reality_evidence/BROAD_REALITY_EVIDENCE_PROTOCOL.md
empirical/broad_reality_evidence/HIERARCHICAL_EVIDENCE_SYNTHESIS_PROTOCOL_v1.md
empirical/broad_reality_evidence/BROAD_META_ANALYSIS_PROTOCOL.md
empirical/broad_reality_evidence/meta_analysis_intake/FIXED_CORPUS_CAPACITY_V1.md
trait_architecture/broad_reality_evidence.py
trait_architecture/broad_meta_analysis.py
trait_architecture/evidence_yield_meta_analysis.py
scripts/harvest_broad_reality_evidence.py
scripts/run_broad_meta_analysis.py
scripts/run_l1_l2_evidence_yield_meta.py
```

### Part III-A: strict matched-study anchors

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

Strict cases are high-quality anchors. Their scarcity does not invalidate the
broad real-world evidence route, and broad records never become D1/D2 merely by
mentioning all relevant terms.

Key files:

```text
empirical/matched_flower_regime/MATCHED_STUDY_PROTOCOL.md
docs/theory_empirical_identifiability_reassessment.md
trait_architecture/matched_regime_registry.py
```

### Part III-B: compatible quantitative effect strata

Where a study reports or permits recovery of a known effect type, it enters a
route-specific registry as one `study × trait × outcome × model effect` at a
time. Pooling occurs only inside compatible scales and causal designs.

```text
flower colour -> pollinator visitation: log response ratio
flower colour -> floral damage: odds ratio
floral defence treatment -> florivory: log response ratio
flower trait -> fruit set: standardised regression coefficient
```

Raw coefficients are never inserted directly into the fitness score, and shared
cost \(c_{AD}\) remains a sensitivity parameter until allocation/cost evidence
exists.

Key files:

```text
empirical/four_path_effects/FOUR_PATH_EFFECT_PROTOCOL.md
empirical/four_path_effects/four_path_effect_registry.csv
empirical/four_path_effects/INITIAL_EVIDENCE_MAP.md
empirical/four_path_effects/EVIDENCE_STATUS_v0.csv
empirical/four_path_effects/EVIDENCE_ATLAS_v0.md
trait_architecture/four_path_effects.py
examples/audit_four_path_effects.py
```

### Part IV: direct field panels

When broad evidence shows an important channel is common but quantitatively
incompatible, or when a Part I regime is not directly observable in published
studies, build a self-contained panel that measures A, B, pollination,
antagonism, and fitness on shared biological units.

## Interpretation boundary

Interaction records are not fitness effects, and trait associations are not
automatically selection, defence efficacy, or adaptation. Broad evidence can be
reported as:

```text
compatible_with_declared_scenario
contradicts_declared_scenario
not_measured_or_not_identified
```

The project distinguishes floral modules from leaf resource quality and leaf
resistance. Leaf traits or leaf antagonism do not enter the floral A×D result
without an explicit cross-organ bridge.