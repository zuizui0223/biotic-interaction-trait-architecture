# Biotic Interaction Trait Architecture

A theory-to-data research program on how plants organise **attraction**, **defence / accessibility**, and **reproductive assurance** traits under multiple biotic interaction regimes.

## Core question

For a trait architecture

\[
\mathbf z=(A,D,R),
\]

how do regimes of mutualists, antagonists, and plant-material consumers alter the favoured combinations of:

- \(A\): attraction traits — floral display, colour, nectar guide, flower size, nectar, orientation;
- \(D\): defence or access-limiting traits — toughness, LDMC, leaf thickness, spines, sticky secretions, chemical defence, architectural barriers;
- \(R\): reproductive-assurance traits — herkogamy, dichogamy, autonomous selfing, delayed selfing, floral longevity?

The central output is not a universal trade-off. It is a map from interaction regime to trait architecture:

\[
\mathcal I \longmapsto \mathbf z^*.
\]

## Research structure

1. **Theory and simulation** — derive when attraction–defence covariance is positive, negative, or non-identifiable from fitness channels.
2. **Global interaction-network backbone** — test partial observational signatures using plant–pollinator and plant–antagonist networks joined to trait modules, taxonomy, study metadata, and phylogeny.
3. **Campanula attraction–assurance chapter** — connect floral display, pollinator service, and selfing / delayed-selfing compensation.
4. **Cirsium floral-defence chapter** — test how display traits co-vary with involucre, spine, sticky secretion, or other antagonism-facing traits.
5. **Megachile material-use case** — a future mechanistic case, not the current validation backbone because structured public host-use data have not yet been established.

## Data discipline

Interaction records are not fitness effects. Trait associations are not automatically selection, defence efficacy, or adaptation. The empirical program therefore separates:

```text
interaction architecture
→ trait-associated interaction signatures
→ dedicated field/case-study mechanism tests
```

Every candidate network source must pass the normalisation and coverage audit in:

```text
empirical/global_networks/DATA_CONTRACT.md
examples/audit_network_backbone.py
```

## Boundary with eco-genetic-criticality

This repository asks:

\[
\text{biotic interaction regime} \to \text{trait architecture}.
\]

`eco-genetic-criticality` asks:

\[
\text{interaction feedback} \to \text{population/genetic persistence}.
\]

A future bridge may map trait architectures to demography and genetic persistence, but the two models remain separate until that bridge is explicitly defined.
