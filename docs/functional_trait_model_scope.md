# Functional-trait model scope

## Decision

Do **not** extend the simulator by adding one coordinate for every visible plant
trait. The theoretical variables represent functional channels; the empirical
layer tests candidate traits within those channels one by one or as explicitly
predeclared submodules.

The first extension is constrained by evidence and source coverage, not by the
total number of interesting natural-history traits.

## Mapping from observed traits to channels

| Functional channel | Initial observed candidates | Main interaction layer | Global-analysis status |
|---|---|---|---|
| `A_flower` | flower/capitulum size, display size, floral access geometry, nectar reward | pollination; florivory | primary target, subject to trait coverage |
| `B_flower` | bract/involucral spines, floral trichomes, sticky reproductive-structure barriers, flower-specific chemical deterrents | florivory; seed predation; pollination access | biologically central; broad abstract map plus source-direction anchors |
| `Q_leaf` | SLA/LMA, LDMC, leaf N, leaf P, thickness | leaf herbivory | primary leaf target, subject to trait coverage |
| `B_leaf` | toughness, trichomes, leaf spines, latex/resin, comparable chemical deterrents | leaf herbivory | conditional target; likely taxon- or source-limited |

The detailed inclusion and exclusion rules are in
`empirical/functional_traits/TRAIT_EVIDENCE_PROTOCOL.md`.

## What changes in the theory

The present qualitative score contains a single generic defence investment `D`.
That remains useful as a minimal model, but its active empirical interpretation is
restricted:

```text
A  -> A_flower
D  -> B_flower in the direct A-D interaction result
```

The current exact `d²W/dA dD` condition therefore describes a floral
attraction--floral barrier relation. It does **not** automatically describe an
association between floral display and leaf toughness, leaf spines, or leaf
nutrient content.

The broad L1/L2 abstract map can describe where the corpus mentions relevant
flower-trait and interaction channels. It cannot bridge floral `A_flower` to leaf
traits, turn candidate co-mentions into a model parameter, or identify a shared
allocation cost. The explicit theory interface is documented in
`docs/broad_evidence_to_regime_interface.md`.

Before adding leaf channels to the score, a future PR must declare one of these
bridges explicitly:

1. **shared allocation bridge**: investment in `A_flower`, `B_flower`, `Q_leaf`,
   or `B_leaf` shares a stated resource budget;
2. **shared developmental bridge**: traits are linked by a stated architectural
   or allometric mechanism;
3. **cross-organ herbivore bridge**: a consumer or damage pathway connects leaf
   condition to floral success; or
4. **no bridge**: leaf modules are modelled as independent responses to leaf
   herbivory, with no predicted covariance with floral attraction.

Without one of these bridges, fitting a global correlation between floral and
leaf traits is descriptive only and must not be called a prediction of the
current model.

## Staged simulation roadmap

### M0: current minimal floral-interaction model

```text
A_flower
B_flower (represented by D)
R as theoretical sensitivity term
P pollinator service
H floral antagonism
L leaf-consumer pressure
```

Use M0 to derive and stress-test conditions for floral complementarity versus
substitution.

### M1: independent leaf-quality and leaf-resistance response

Add `Q_leaf` and `B_leaf` only after the network and trait audits demonstrate
usable coverage. M1 first asks:

```text
Q_leaf, B_leaf <-> leaf-herbivore interaction structure
```

It does not yet assert an attraction--leaf-defence trade-off.

### M2: cross-organ architecture model

Add an explicit bridge only after a biologically matched dataset supports it.
This may represent an allocation cost, a shared organ-level architecture, or a
particular cross-organ consumer pathway. M2 is not justified by assembling
unmatched global pollination and herbivory databases.

## Explicit v1 exclusions

- leaf mottling / variegation;
- generic leaf-shape or lobing defence claims;
- stem/wood resistance and Cerambycidae;
- leaf-cutting bee material suitability;
- any composite "defence score" that mixes floral, leaf, stem, structural, and
  chemical traits.

These may become focused future modules, but their inclusion requires a direct
functional hypothesis, an appropriate consumer layer, and data coverage.
