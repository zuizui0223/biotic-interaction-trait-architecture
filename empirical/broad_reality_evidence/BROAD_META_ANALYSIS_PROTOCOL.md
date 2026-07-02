# Broad real-world evidence: floral trait--animal response synthesis v2

## Position in the research program

```text
Part I   attraction--defence regime mathematics and sensitivity map
Part II  calibrated broad L1/L2 evidence map and full-text screening universe
Part III route-specific floral trait--animal response effect-size syntheses
Part IV  direct floral-defence experiments as high-causal-confidence confirmation
```

Part III replaces the earlier idea that the only quantitative synthesis should
be direct floral-defence manipulations. Direct B-flower experiments remain an
important subset, but the primary quantitative design now uses every eligible
flower-trait study that measures an animal response and has a recoverable effect
size.

The synthesis never estimates universal coefficients for Part I. It tests
whether the empirical direction and magnitude of each route vary by trait role,
animal outcome, study design, and ecological context.

## Four route-specific questions

| Route | Question | Direction expected by the current model |
|---|---|---|
| `A_to_pollinator` | Does higher floral attraction increase pollinator response? | positive (`b_A`) |
| `A_to_antagonist` | Does higher floral attraction increase floral-antagonist response? | positive (`d_A`) |
| `B_to_antagonist` | Does stronger flower-specific barrier/deterrence reduce antagonist response? | negative (`e_F`) |
| `B_to_pollinator` | Does stronger flower-specific barrier/deterrence reduce pollinator response? | negative (`c_D`) |

A contrary sign is retained as evidence of a trait-role, context, or regime
boundary. It is never reversed merely to agree with the theory.

## Unit of evidence

```text
candidate unit        fixed-corpus abstract carrying a flower-context A/B × P/H edge
screening unit        candidate work × candidate route
extraction unit       effect_id from a full-text study
analysis unit         independent study × route × design × outcome family × effect family
```

Multiple papers, traits, time points, or models from one data-generating panel
are not independent replicates. Version 1 uses one prespecified primary effect
per independent study in each analysis unit. Dependence-aware multilevel models
are a future extension, not an implicit assumption.

## Eligibility

An effect enters the quantitative layer only when all conditions hold:

1. the focal trait is assigned to `A_flower` or `B_flower`;
2. the trait is measured or manipulated on a flower, inflorescence, nectar, or
   reproductive structure;
3. the response is pollinator or floral-antagonist specific;
4. the design is a direct experiment, a choice assay, or an observational
   association;
5. a compatible effect size and variance are recoverable;
6. independent study identity can be declared.

Leaf, stem, bark, wood, root, and unlocalized whole-plant defence evidence is
not B-flower evidence. Pigment, scent, morphology, or compatibility studies
without an animal-response measurement are not quantitative route records.

## Designs and effect families

| Study design | Allowed effect families in v1 | Pooling boundary |
|---|---|---|
| direct experiment | log response ratio, Hedges' g, log odds ratio, log rate ratio | exact route × outcome family × effect family |
| choice assay | Hedges' g, log odds ratio, log rate ratio | exact route × outcome family × effect family |
| observational association | Fisher's z, converted from a declared trait--response association | never pooled with experimental or choice effects |

All effects are oriented so a positive value means that greater focal trait value
or the high-trait treatment increases the measured animal response: visitation,
foraging, attack, or damage. Thus A→P and A→H are model-compatible when
positive, whereas B→H and B→P are model-compatible when negative.

## Quantitative outputs

The first outputs are forest plots and route-specific summaries inside each:

```text
route × study_design × outcome_family × effect_family
```

```text
k < 2 independent studies    narrative evidence only
2 <= k < 5                   forest plot and descriptive uncertainty; no primary pooled claim
k >= 5                       random-effects summary eligible
```

No primary summary pools:

- observational Fisher-z associations with experimental or choice effects;
- visitation/choice with pollen transfer or reproductive output;
- floral damage with antagonist abundance unless explicitly declared as the same
  outcome family;
- different organs;
- multiple primary effects from the same independent study.

## Broad map and confirmation layer

The broad L1/L2 corpus is retained as a calibrated discovery and missingness map.
It supplies a fixed full-text queue but never supplies numerical effect sizes.
Automatic abstract tiers only determine reading order.

Direct B-flower manipulation studies are tagged during extraction and reported
as a high-causal-confidence sensitivity subset. They test the original narrow
question without forcing the entire empirical program to depend on its small
candidate set.

## Relation to Part I

The current regime condition remains unchanged:

```text
∂²W/∂A∂D = H*d_A*e_F - P*b_A*c_D*exp(-c_D*D)*(1-c_R*R) - c_AD
```

Route-specific syntheses can determine whether signs are supported in defined
contexts and which trait/outcome cells are data-poor. They do not identify `P`,
`H`, `c_AD`, or `c_R`, and they cannot infer A--B covariance by combining
separate route analyses.

The detailed full-text screening and extraction contract is in
`FLORAL_TRAIT_ANIMAL_RESPONSE_META_PROTOCOL_v1.md`.
