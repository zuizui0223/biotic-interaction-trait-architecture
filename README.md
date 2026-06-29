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

1. **Part I — theory and simulation.** Derive exact local conditions under which
   floral attraction and floral barriers are complementary, substitutable, or
   neutral in the declared score; report parameter regions where the simulated
   association is stable versus mixed.
2. **Part II — reproducible data-route decisions.** Test whether public sources
   can actually supply the matched unit required for an empirical analysis.
3. **Part III — matched floral-study synthesis.** Test predeclared Part I
   observation models only with studies that measure floral traits, pollination,
   and floral antagonism in the same biological context.

```text
Part I: model assumptions → exact conditions → simulation phase map
Part II: source feasibility → accepted or retired data routes
Part III: matched study panels → compatible / contradicts / not identified
```

The score retains reproductive assurance `R` as a sensitivity term because it can
dilute the outcross return of attraction. There is no separate global empirical
`R` module in this first program.

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

A direct test of the current Part I \(A_{flower} \times B_{flower}\) result
requires a study panel with:

```text
floral attraction trait(s)
+ floral barrier/resistance trait(s)
+ pollination response with denominator
+ floral-antagonist response with denominator
+ same site/time or predeclared overlap
+ a declared linkage unit
+ recoverable table and trait method
```

The unit is a **study landscape**, not a species name pooled across unrelated
databases. Evidence is classified before modelling:

```text
M0  candidate requiring full-text screen
M1  one-channel or unaligned evidence ledger
M2  aligned two-channel panel, but incomplete for a direct test
D1  direct-regime model candidate
```

Files for this active route:

```text
empirical/matched_flower_regime/MATCHED_STUDY_PROTOCOL.md
empirical/matched_flower_regime/literature_seed_queries.csv
empirical/matched_flower_regime/matched_flower_study_cards.csv
examples/audit_matched_flower_studies.py
trait_architecture/matched_regime_registry.py
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
→ dedicated mechanism tests
```

A D1 result can be called only `compatible_with_declared_scenario`,
`contradicts_declared_scenario`, or `not_identified`. It is not proof of
adaptation unless fitness or selection data are separately included.

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
