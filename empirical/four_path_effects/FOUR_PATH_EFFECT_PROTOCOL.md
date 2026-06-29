# Four-path effect-size synthesis protocol

## Purpose

Ideal D2/D3 panels may be rare. The fallback is **not** to pool unmatched traits
or call a literature count a theory test. Instead, collect direct effect sizes
for the four links required by Part I:

```text
A_flower → pollination            b_A
A_flower → floral antagonism      d_A
B_flower → floral antagonism      e_F
B_flower → pollination            c_D
```

The registry stores one row per **study × trait × outcome × reported model
effect**. It supports later scale-specific meta-analysis and parameter envelopes
for the Part I robustness sweep.

## What this synthesis can and cannot do

It can estimate how often and how strongly each directional trait–interaction
link appears across comparable studies. It can then constrain plausible ranges
for the two biological channel terms in the score.

It cannot, by itself:

- estimate the exact shared allocation cost `c_AD`;
- establish a direct A×B fitness curvature;
- turn a raw observational association into causal adaptation; or
- merge effects measured on incompatible scales without a declared conversion.

```text
four separate effect distributions
→ empirically informed parameter envelopes
→ robustness-conditioned regime map

not

four pooled columns
→ proof of the exact fitness equation
```

## Required inclusion rule

A row is eligible only when all of the following are explicit in the primary
study or its recoverable supplement/repository:

```text
1. a directly measured floral trait;
2. trait role assigned as A_flower or B_flower before inspecting the effect sign;
3. a direct pollination or floral-antagonist outcome;
4. effect estimate and uncertainty, or a recoverable table sufficient to compute it;
5. unit, site/context, and sampling period or a declared equivalent;
6. outcome denominator/exposure when the response is a rate, proportion, count, or binary event.
```

Leaf traits, leaf antagonism, and cross-study taxon joins are out of scope unless
a separate predeclared cross-organ bridge is introduced.

## Four effect roles

| effect_role | Trait module | Outcome channel | Model parameter informed |
|---|---|---|---|
| `A_to_pollination` | `A_flower` | `pollination` | `b_A` |
| `A_to_antagonism` | `A_flower` | `floral_antagonism` | `d_A` |
| `B_to_antagonism` | `B_flower` | `floral_antagonism` | `e_F` |
| `B_to_pollination` | `B_flower` | `pollination` | `c_D` |

The role is checked from the trait-module and outcome-channel fields. It is not
assigned from a paper title or an author conclusion.

## Outcome and denominator rules

### Pollination

Permitted outcomes include standardised visitor rate, pollen deposition/transfer,
outcrossing proxy, pollinator effectiveness, fruit set, or viable seed outcome
only when the study explicitly links it to pollination.

```text
visitor count       → observation minutes/hours or flower exposure required
pollen count        → flowers/stigmas sampled required
fruit/seed response → flowers, fruits, ovules, or marked plants at risk required
```

### Floral antagonism

Permitted outcomes include flower damage, florivory incidence, tissue loss,
pre-dispersal seed predation, nectar robbery, pollen theft, or another direct
flower-stage antagonist response.

```text
damage incidence    → flowers/heads/individuals inspected required
seed predation      → intact + damaged seed denominator required
visitor/robber rate → observation exposure required
```

## Effect-scale discipline

The registry does not silently transform or pool estimates. Every row declares
one of:

```text
standardized_regression_slope
log_response_ratio
log_odds_ratio
incidence_rate_ratio
rate_ratio
standardized_mean_difference
fisher_z
other_reported
```

A row is `parameter_bridge_ready` only when the effect is either:

```text
1. a standardized slope with a declared trait scaling and response link; or
2. recoverable from a raw table under a predeclared conversion model.
```

All other effects remain valuable for scale-specific synthesis, but do not enter
a common numerical parameter envelope until converted transparently.

## Causal-status discipline

```text
manipulated          trait or intervention is experimentally altered
quasi_experimental   a defensible natural intervention/assignment is declared
observational        conditional association only
not_assessed         before full-text screen
```

Do not use an observational effect as a causal parameter without a separate
identification argument. The default parameter-envelope analysis reports causal
and observational evidence separately.

## Hierarchical synthesis plan

For each effect role and compatible scale, fit a study-aware hierarchical model:

```text
effect ~ overall role-specific mean
       + trait-class moderator
       + floral-antagonist type / pollination outcome moderator
       + design-type moderator
       + study random effect
       + species/context random effect when identifiable
```

The first analysis does not force a shared mean across effect scales. It reports:

```text
role × effect-scale × design-type distributions
```

Only after a declared harmonization rule is validated may compatible effects form
a parameter envelope for `b_A`, `d_A`, `e_F`, or `c_D`.

## Relation to direct cases

D2/D3 studies are entered into this registry **and** retained as individual case
validation. They are not allowed to dominate the meta-analysis merely because
they contain more outcomes.

## Current priority

Screen in this order:

```text
1. manipulation with flower-level reproductive fitness
2. individual-level A/B trait studies with both channels
3. direct effect studies for under-filled paths
4. high-information M2 panels as source studies for one or more effects
```

A literature route has succeeded when it produces transparent, role-specific
effect distributions—even if no single study reaches D2 or D3.