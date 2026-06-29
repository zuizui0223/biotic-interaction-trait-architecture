# Biotic Interaction Trait Architecture

A theory-to-data research program on how plants organise **attraction** and
**defence / accessibility** traits under contrasting biotic interaction regimes.

## Core question

For a trait architecture

\[
\mathbf z=(A,D),
\]

how do mutualist and antagonist regimes alter the favoured combinations of:

- \(A\): attraction traits — floral display, colour, nectar guide, flower size, nectar, orientation;
- \(D\): defence or access-limiting traits — toughness, LDMC, leaf thickness, spines, sticky secretions, chemical defence, architectural barriers?

The central output is not a universal trade-off. It is a conditional map from
interaction regime to trait architecture:

\[
\mathcal I \longmapsto \mathbf z^*.
\]

## Active research structure

1. **Theory and simulation** — derive the conditions under which attraction and defence are locally complementary, substitutable, or not identified by the current model; then test whether those conclusions are stable across declared parameter scenarios.
2. **Global interaction-network backbone** — test predeclared observational signatures using plant--pollinator and plant--antagonist networks joined to direct trait modules, taxonomy, study metadata, and phylogeny.

The active program is therefore:

```text
model assumptions
→ exact local conditions and simulation sensitivity
→ source-resolved global-network signatures
→ explicit support, contradiction, or non-identifiability
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
