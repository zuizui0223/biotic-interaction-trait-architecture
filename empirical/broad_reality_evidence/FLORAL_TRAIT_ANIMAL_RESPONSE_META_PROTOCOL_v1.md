# Floral trait--animal response effect-size synthesis v1

## Why this replaces the narrow primary meta-analysis

The earlier narrow question was: does a direct manipulation of floral defence
change pollination or floral antagonism? It is causally clean but too sparse to
serve as the only quantitative empirical analysis.

The primary quantitative synthesis is now broader:

```text
predeclared floral trait channel (A_flower or B_flower)
        ×
predeclared animal-response layer (pollinator or floral antagonist)
        ×
study design and effect-size family
```

Direct floral-defence experiments remain a high-causal-confidence confirmation
layer. They are not discarded.

## The four route-specific questions

| Route | Trait channel | Animal response | Direction convention | Model connection |
|---|---|---|---|---|
| A→P | `A_flower` | pollinator visitation, choice, pollen transfer | positive = higher A increases pollinator response | `b_A` |
| A→H | `A_flower` | floral-antagonist attack, damage, or use | positive = higher A increases antagonist response | `d_A` |
| B→H | `B_flower` | floral-antagonist attack, damage, or use | negative = higher B reduces antagonist response | `e_F` |
| B→P | `B_flower` | pollinator visitation, choice, pollen transfer | negative = higher B reduces pollinator response | `c_D` |

The meta-analysis estimates route-specific empirical effects. It does **not**
fit the attraction--defence score or identify the shared-cost term `c_AD`.

## Trait scope

### A_flower: include

- flower, capitulum, or inflorescence display size;
- floral colour or visual contrast when measured as a pollinator/antagonist cue;
- floral scent and reward traits when their interaction role is measured;
- access geometry when it functions as an attraction or reward-use trait.

### B_flower: include only with flower-organ evidence

- nectar secondary metabolites and nectar deterrence;
- floral/inflorescence trichomes, sticky secretions, bracts, spines, and physical barriers;
- floral chemical deterrents;
- opening/closure or reproductive-structure access restrictions **only when a
  stated floral-antagonist deterrence or pollinator-access mechanism is tested**;
- cryptic floral colour only when floral-antagonist avoidance is explicitly
  measured or experimentally tested.

### Exclude from the direct A--B synthesis

- leaf, stem, bark, root, and wood resistance;
- generic whole-plant defence without an organ-specific floral bridge;
- pollination syndrome labels;
- self-incompatibility and post-pollination compatibility systems;
- pigment, scent, or morphology studies with no animal-response measure.

## Eligible designs and effect families

| Design | Primary effect family | Examples | Pooling rule |
|---|---|---|---|
| direct experiment | log response ratio, Hedges' g, log odds ratio, log rate ratio | trait addition/removal, nectar chemistry treatment, barrier exclusion | pool only within route × outcome family × effect family |
| choice assay | log odds ratio, log rate ratio, Hedges' g | paired floral choices, preference tests, visitation allocation | pool only within route × outcome family × effect family |
| observational association | Fisher's z | trait--visitation, trait--damage, trait--attack correlations/regressions converted to r | never pool with experimental effects in v1 |

The sign convention always refers to increasing the focal trait or moving from
low to high treatment. It always refers to an increase in the animal response:
use, visitation, attack, or damage. Thus the route interpretation is preserved
without algebraically reversing some outcomes during extraction.

## Full-text inclusion gate

A candidate effect is included only if all conditions hold:

1. focal trait is assigned to `A_flower` or `B_flower`;
2. trait is measured or manipulated on a flower, inflorescence, nectar, or
   reproductive structure;
3. the animal response is pollinator or floral-antagonist specific;
4. design is direct experiment, choice assay, or observational association;
5. a compatible effect size and sampling variance can be extracted or calculated;
6. its independent study cluster can be identified;
7. outcome family and effect family are declared before pooling.

Each article can supply several effects, but only one `is_primary_effect_for_study`
row per independent study can enter a v1 random-effects group. Other effects are
retained for future multilevel models or sensitivity analyses.

## Pooling rules

The first quantitative outputs are separate forest plots and random-effects
summaries for each nonempty:

```text
route × study_design × outcome_family × effect_family
```

A pooled v1 estimate requires at least five independent studies. Groups with two
to four independent studies get forest plots and descriptive uncertainty only;
groups with fewer than two are narrative case evidence. A statistical estimate
must never combine:

- Fisher-z observational associations with experimental effect sizes;
- visitation/choice outcomes with reproductive output;
- floral damage with antagonist abundance unless declared as one outcome family;
- different organs;
- multiple primary effects from the same independent study.

## Broad map and direct-defence confirmation layer

The fixed L1/L2 broad map remains the literature-coverage layer. The full-text
queue contains every fixed-corpus flower-context abstract carrying at least one
candidate A/B × P/H edge. Its automatic tiers only prioritise reading order; they
are not evidence grades.

Direct B_flower experiments are tagged during extraction and reported as a
high-causal-confidence sensitivity subset. This preserves the original question
without making the whole analysis depend on its small current candidate set.

## Relation to the regime model

The regime model remains unchanged:

```text
∂²W/∂A∂D = H*d_A*e_F - P*b_A*c_D*exp(-c_D*D)*(1-c_R*R) - c_AD
```

The meta-analysis can inform whether route-specific signs are empirically
supported in defined contexts, and can compare relative magnitudes only within
compatible outcome/effect families. It does not estimate `P`, `H`, `c_AD`, or
`c_R`, and it must not infer an A--B covariance from separate route analyses.
