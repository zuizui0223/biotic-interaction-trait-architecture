# Biotic Interaction Trait Architecture

A theory-to-data research program on how plants organise **floral attraction**,
**floral barriers**, **leaf resource quality**, and **leaf resistance** under
contrasting biotic interaction regimes.

## Core question

For a trait architecture

\[
\mathbf z=(A,D),
\]

how do mutualist and antagonist regimes alter the favoured combinations of
functional trait modules?

- \(A\): flower-facing attraction and access — floral display, size, reward, geometry, colour/contrast, orientation;
- \(D\): a deliberately abstract resistance/access-limitation channel. In empirical work it is split by organ and mechanism rather than filled with a single pooled defence score.

The central output is not a universal trade-off. It is a conditional map from
interaction regime to trait architecture:

\[
\mathcal I \longmapsto \mathbf z^*.
\]

## Active research structure

1. **Part I — theory and robustness simulation.** Derive exact local conditions
   under which floral attraction and floral barriers are complementary,
   substitutable, or neutral; then test whether the sign persists across
   alternative response curves and parameter scenarios.
2. **Part II — reproducible data-route decisions.** Test whether public sources
   can actually supply the matched unit required for an empirical analysis.
3. **Part III — four-path effect synthesis and direct cases.** Quantify the
   separate attraction/barrier effects on pollination and floral antagonism,
   while retaining exceptional D2/D3 studies as individual validation cases.

```text
Part I: model assumptions → exact conditions → functional-form robustness map
Part II: source feasibility → accepted or retired data routes
Part III: four path-specific effect distributions → parameter envelopes → empirical regime map
```

The score retains reproductive assurance `R` as a sensitivity term because it can
dilute the outcross return of attraction. There is no separate global empirical
`R` module in this first program.

## Part I: robustness before calibration

The baseline score is intentionally qualitative. Before empirical effect sizes
are used to constrain its parameters, the project tests whether the local
attraction–barrier mixed partial survives:

```text
baseline linear responses
+ saturating pollination benefit from attraction
+ saturating defence efficacy against floral antagonists
+ curved shared attraction–defence cost
+ low / baseline / high channel-strength scenarios
```

The output is not a universal prediction. Each local regime point is labelled:

```text
structurally_robust
conditional_majority
mixed_or_sensitive
```

Files:

```text
docs/PART_I_ROBUSTNESS_PROTOCOL.md
configs/part_i_robustness_grid.json
trait_architecture/robustness.py
scripts/run_part_i_robustness.py
```

## Part II result: do not force a global database join

The first public global join has been tested and **is not the active empirical
backbone**:

```text
Web of Life × BIEN leaf traits
  → insufficient trait-provider row coverage on the reproducible screen

GloBI plant–antagonist API claims
  → lacks the sampled-network identity and effort contract

TRY custom export
  → optional future infrastructure, not a reproducible active dependency
```

These are data-route decisions, not negative evidence for the Part I model. The
project does not replace failed coverage with manual taxon filling, imputation,
or unmatched joins.

## Direct empirical route: matched floral studies

The exact Part I result concerns local **fitness curvature**, not observed trait
covariance. A direct empirical route therefore needs more than A/B traits and
two interaction responses. It must establish the four directional paths:

```text
A_flower → pollination
A_flower → floral antagonism
B_flower → floral antagonism
B_flower → pollination
```

and, for a direct observed-curvature comparison, a linked reproductive-fitness
response.

```text
M0  candidate requiring full-text screen
M1  one-channel or unaligned evidence ledger
M2  aligned two-channel panel, but one or more Part I paths unestimated
D1  four-arrow channel-mechanism panel
D2  D1 plus observed reproductive-fitness surface
D3  D2 plus independently observed/calibrated A×B shared cost
```

The unit is a **study landscape**, not a species name pooled across unrelated
databases. A D1 panel can identify the interaction-channel balance; only D2/D3
can compare an observed A×B fitness curvature with a declared Part I scenario.

Files for this direct-case route:

```text
empirical/matched_flower_regime/MATCHED_STUDY_PROTOCOL.md
docs/theory_empirical_identifiability_reassessment.md
empirical/matched_flower_regime/literature_seed_queries.csv
empirical/matched_flower_regime/matched_flower_study_cards.csv
examples/audit_matched_flower_studies.py
trait_architecture/matched_regime_registry.py
```

## Broad empirical route: four-path effect synthesis

Ideal D2/D3 panels may be rare. The broad empirical route therefore retains one
study × trait × outcome effect at a time and never treats a literature count as
a theory test.

```text
A_flower → pollination            b_A
A_flower → floral antagonism      d_A
B_flower → floral antagonism      e_F
B_flower → pollination            c_D
```

Effects remain separate by outcome scale and design type until a declared
harmonization rule is justified. They then constrain **parameter envelopes** for
the Part I robustness sweep; raw coefficients are never silently inserted into
the fitness score. The shared cost `c_AD` remains a sensitivity parameter unless
an independent allocation/cost measure is available.

Files:

```text
empirical/four_path_effects/FOUR_PATH_EFFECT_PROTOCOL.md
empirical/four_path_effects/four_path_effect_registry.csv
trait_architecture/four_path_effects.py
examples/audit_four_path_effects.py
```

## Functional-trait discipline

The empirical layer distinguishes four functional channels:

```text
A_flower  floral attraction and visitor access
B_flower  floral/reproductive-structure barriers and florivore resistance
Q_leaf    leaf construction and resource quality
B_leaf    leaf structural or chemical resistance
```

This prevents three category errors:

- leaf economics traits such as SLA, LDMC, and leaf N are not automatically
  labelled "defence";
- floral bract spines and leaf spines are not pooled despite being visually
  similar; and
- leaf mottling, generic leaf shape, stem/wood traits, and leaf-cutting-bee
  material suitability are not promoted into a defence model without a direct
  functional bridge.

The evidence matrix and model-scope decision are maintained in:

```text
empirical/functional_traits/TRAIT_EVIDENCE_PROTOCOL.md
empirical/functional_traits/trait_role_evidence.csv
empirical/functional_traits/literature_seed_registry.csv
docs/functional_trait_model_scope.md
```

## Data discipline

Interaction records are not fitness effects. Trait associations are not
automatically selection, defence efficacy, or adaptation. The empirical program
therefore separates:

```text
interaction architecture
→ trait-associated interaction signatures
→ directional mechanism paths
→ conditional reproductive-fitness curvature
```

D1 identifies channel pathways, not the full Part I sign. D2/D3 results can be
called only `compatible_with_declared_scenario`,
`contradicts_declared_scenario`, or `not_identified`; none is proof of adaptation
without a suitable intervention or identification design.

## Boundary with eco-genetic-criticality

This repository asks:

\[
\text{biotic interaction regime} \to \text{trait architecture}.
\]

`eco-genetic-criticality` asks:

\[
\text{interaction feedback} \to \text{population/genetic persistence}.
\]

A future bridge may map trait architectures to demography and genetic
persistence, but the two models remain separate until that bridge is explicitly
defined.
