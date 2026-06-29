# Public-data-first feasibility gates

## Why this exists

The project will not make a manual, custom trait request a prerequisite for its
first empirical result. A data route has to be reproducible by another person
running the same code against a documented public source.

The immediate output is not an ecological effect estimate. It is a defensible
**go / no-go decision** for each proposed global route.

## Gate 0: theory remains independent

The exact attraction--floral-barrier result and its simulation sensitivity are
research outputs in their own right. They are not held hostage by external trait
coverage.

## Gate 1: automated leaf-trait access

For a declared, versioned public trait provider:

1. retrieve records by script for a reproducible test set of plant taxa;
2. request only `sla`, `ldmc`, `leaf_n_mass`, `leaf_p_mass`, and
   `leaf_thickness` at first;
3. retain provider taxon, record identifier, unit, observation level, and
   provenance;
4. run the direct-record coverage audit; and
5. reject the provider for the primary route if the declared threshold fails.

This test answers only: **can this source supply leaf functional traits without a
manual data request?** It does not yet test herbivory.

## Gate 2: automated antagonist-network access

For each candidate public interaction source:

1. retrieve edges and network metadata by script;
2. retain only explicit plant--antagonist interaction types;
3. require network ID, region, plant taxon, animal taxon, source provenance,
   and sampling period where available;
4. test whether at least 30 independent, geographically distributed networks
   remain after normalisation; and
5. reject the source as a broad backbone when the contract fails.

Occurrence-only interaction aggregators may be useful for discovery but do not
by themselves supply an effort-controlled network backbone.

## Gate 3: joint leaf route

Only after Gates 1 and 2 pass do we join the sources and evaluate:

```text
Q_leaf (leaf construction/resource quality)
  ↔
plant--antagonist network signatures
```

The joint analysis is a partial observational test. It does not validate the
floral attraction--floral-barrier cross-partial and does not establish selection.

## Floral route

The floral route is deliberately separate:

```text
pollination edges + floral traits measured in the same study
```

A global taxon join is not attempted. The unit is a matched study/network, with
floral traits read from its table, supplement, repository, or a linked public
dataset. Studies with edges but no measured floral traits may support network
description, but not a floral-trait model.

## Decision outcomes

| Result | Project action |
|---|---|
| Gates 1 and 2 pass | Run the predeclared leaf-quality/antagonist analysis. |
| Gate 1 passes, Gate 2 fails | Retain leaf traits for a later matched-study analysis; do not fabricate a herbivory backbone. |
| Gate 1 fails | Do not substitute a manual TRY export; pivot to matched studies. |
| Floral matched studies accumulate | Run a study-level floral-trait synthesis separately from the leaf route. |
| Neither empirical route passes | Publish/advance the theory and simulation as the completed first unit; empirical data feasibility is itself a documented negative result. |

## Immediate next action

Run **Gate 1** with the existing script-accessible BIEN interface on leaf traits,
not floral traits. The output must be a saved coverage report, not a claim that
BIEN is an adequate empirical backbone. In parallel, inventory candidate public
antagonist-network sources against Gate 2 before writing any interaction model.
