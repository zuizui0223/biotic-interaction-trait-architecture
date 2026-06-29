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

1. **Theory and simulation** — derive the conditions under which attraction and defence are locally complementary, substitutable, or not identified by the current model; then test whether those conclusions are stable across declared parameter scenarios.
2. **Global interaction-network backbone** — test predeclared observational signatures using plant--pollinator and plant--antagonist networks joined to direct functional-trait modules, taxonomy, study metadata, and phylogeny.

The active program is therefore:

```text
model assumptions
→ exact local conditions and simulation sensitivity
→ source-resolved global-network signatures
→ explicit support, contradiction, or non-identifiability
```

The current score retains reproductive assurance `R` as a sensitivity term because
it can dilute the outcross return of attraction. There is no separate empirical
`R` module in this first study; it is varied in theory rather than treated as a
third global-data target.

## Functional-trait discipline

The empirical layer distinguishes four functional channels:

```text
A_flower  floral attraction and visitor access
B_flower  floral/reproductive-structure barriers and florivore resistance
Q_leaf    leaf construction and resource quality
B_leaf    leaf structural or chemical resistance
```

This prevents three common category errors:

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

## Trait receipt and coverage gate

A provider request, a downloaded export, and a model-ready trait table are kept
separate. Trait-specific coverage is audited against the requested Web of Life
plant set before modelling. Direct records and imputed values are reported
separately; only direct records count toward primary-analysis readiness.

```text
empirical/functional_traits/TRY_REQUEST_SCOPE.md
empirical/functional_traits/TRAIT_RECEIPT_CONTRACT.md
empirical/functional_traits/trait_receipt_template.csv
empirical/functional_traits/trait_source_registry_template.csv
examples/audit_trait_receipt_coverage.py
```

## Future cases, outside the present backbone

Campanula, Cirsium, and Megachile remain possible future mechanistic cases. They
are not necessary for the first theory-plus-global-data study and are not used as
the current empirical validation backbone.

## Data discipline

Interaction records are not fitness effects. Trait associations are not
automatically selection, defence efficacy, or adaptation. The empirical program
therefore separates:

```text
interaction architecture
→ trait-associated interaction signatures
→ future dedicated mechanism tests
```

Every candidate network source must pass the normalisation and coverage audit in:

```text
empirical/global_networks/DATA_CONTRACT.md
docs/theory_to_network_prediction_contract.md
examples/audit_network_backbone.py
```

The theory-to-network contract also distinguishes exact conclusions for the
implemented score from simulation summaries and from empirical trait
associations. In particular, a positive or negative A--D association observed in
a dataset is not automatically evidence for a named interaction mechanism.

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
