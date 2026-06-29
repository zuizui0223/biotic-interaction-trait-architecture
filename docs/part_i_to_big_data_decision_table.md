# Part I theory → empirical decision table

## Purpose

Part I derives exact and simulated conclusions for a declared fitness score.
Later empirical work must not merely collect large datasets: it must determine
which **predeclared paths and fitness layers** are identifiable from a study.

This prevents two overclaims:

1. treating any global trait correlation as a test of the attraction–barrier
   model; and
2. treating a matched A/B/pollination/antagonism table as though it already
   identified the Part I mixed partial.

## What Part I actually predicts

For the current score, local attraction–defence complementarity is determined
by:

```text
floral-antagonist tracking × floral-barrier efficacy
  versus
pollinator-access obstruction + shared A–D cost
```

The exact mixed partial concerns `A_flower` and `B_flower`:

\[
\frac{\partial^2 W}{\partial A\,\partial D}
=
H d_A e_F
-
P b_A c_D e^{-c_DD}(1-c_RR)
-
c_{AD}.
\]

Leaf-consumer pressure may change leaf investment or overall allocation, but it
does not directly enter this floral mixed partial.

## Step zero: functional-form robustness

Before empirical effects constrain any parameter range, Part I must identify
which local signs survive changes in response curvature. The predeclared sweep
varies:

```text
attraction benefit: linear versus saturating
barrier efficacy: linear versus saturating
shared A×B cost: linear versus escalating
channel strengths: low / baseline / high scenarios
P, H, R, A, D: local regime and phenotype grid
```

The result is a **qualitative robustness map**:

```text
structurally_robust
conditional_majority
mixed_or_sensitive
```

This step does not use literature effect sizes and does not claim calibration.
It determines which model signatures are worth confronting with data.

## Evidence levels for direct cases

| Evidence level | Required unit and data | What it can judge | What it cannot judge |
|---|---|---|---|
| **D3 Parameterized score panel** | D2 plus independent shared allocation cost or a transparent validated calibration | full comparison to the declared Part I expression | causal adaptation without an intervention/identification design |
| **D2 Observed fitness-surface panel** | D1 plus linked reproductive-fitness response and denominator | conditional observed A×B fitness curvature, compatible/contradictory/not-identified for a scenario | separate attribution of residual shared cost |
| **D1 Channel-mechanism panel** | same plant/context; separately measured A/B; both channels; denominators; and estimable `A→P`, `A→H`, `B→H`, `B→P` paths | sign and magnitude of the two biological channel terms under the observation model | the total Part I sign without fitness/cost |
| **M2 Aligned two-channel panel** | same context; A/B traits; pollination and antagonist observations; but one or more directional paths unestimated | component-level joint association and future D1 acquisition target | Part I mixed partial or a trade-off claim |
| **M1 Channel ledger** | a direct floral trait plus either pollination or floral-antagonist observation | one mechanism link | the other channel or Part I cross-partial |
| **C1 Attraction component test** | pollination edges and direct floral traits within a study/network | whether a floral-trait module is associated with mutualist-network structure | floral defence, florivory, or the Part I cross-partial |
| **C2 Leaf-antagonist component test** | explicit plant–leaf-antagonist network and direct leaf quality/resistance traits | whether `Q_leaf`/`B_leaf` is associated with leaf-antagonist structure | floral A×B result without an explicit cross-organ bridge |
| **C3 Source feasibility result** | trait/interaction source that passes or fails access and metadata gates | whether a data route is reproducibly available | any biological effect or theory sign |
| **N0 Non-test** | unmatched databases, imputed traits, or pairwise claims without sampled units | nothing about the Part I sign | a trade-off, complementarity, or absence of evidence |

## Broad evidence synthesis: four separate paths

When ideal D2/D3 studies are rare, the broad empirical route does not stop. It
collects separate direct effects for the four arrows:

```text
A_flower → pollination            b_A
A_flower → floral antagonism      d_A
B_flower → floral antagonism      e_F
B_flower → pollination            c_D
```

Each registry row is `study × trait × outcome × reported model effect`. Effects
stay separated by scale and design type until a conversion is declared. The
result is a role-specific parameter envelope, not a single pooled “trade-off”
effect.

```text
role × effect scale × design type distributions
→ parameter envelopes for robustness scenarios
→ empirically informed regime map
```

`c_AD` remains a sensitivity parameter until a direct allocation-cost measure or
validated calibration exists.

## Decision rules

### Direct support / contradiction / non-identifiability

A D2 or D3 analysis may be labelled:

- **compatible with scenario S** when its preregistered observation model yields
  the expected direction under sampling and phylogenetic sensitivity checks;
- **contradicts scenario S** when the opposite direction is robust and proxy
  mapping/sampling are adequate; or
- **not identified** when any directional path, trait coverage, matched layer,
  denominator, sampling requirement, or fitness condition fails.

D1 may identify a channel balance but never the full score sign. No level may be
called proof of adaptation without a fitness/selection component and suitable
identification design.

### The four-arrow requirement

A matched table becomes a D1 candidate only after all four paths are estimable:

```text
A_flower → pollination            b_A
A_flower → floral antagonism      d_A
B_flower → floral antagonism      e_F
B_flower → pollination            c_D
```

Observed florivory does not establish `d_A`; a floral defence trait does not
establish `c_D`; and raw trait covariance establishes none of the four arrows.
The shared allocation term `c_AD` requires a D2 fitness surface or D3
cost/calibration layer.

### How C1 and C2 contribute

C1 and C2 remain useful evidence about individual links in the mechanism map.
They can narrow plausible parameter regimes or motivate a future D1 test, but
they do not substitute for D1:

```text
leaf quality ↔ herbivory structure
≠
floral attraction × floral barrier complementarity
```

### Immediate data-source consequence

The public-data probes remain C3 feasibility tests:

1. BIEN leaf records test whether a public `Q_leaf` route can exist.
2. GloBI contract screening tests whether public antagonist claims have the
   sampled-network metadata required for a C2 route.
3. Matched floral studies are screened for M0–D3 rather than being forced into a
   single direct-test category.
4. Four-path effect records are screened separately for scale-compatible
   synthesis and parameter-envelope readiness.

## Publication logic

```text
Part I: exact conditions + functional-form robustness map
Part II: public-data feasibility and component analyses
Part III: four-path synthesis + exceptional D2/D3 case validation
```

The project is successful at each completed level. A failed C3 route or an M2
study with unresolved arrows is an identifiability finding, not an excuse for
manual filling or post hoc trait pooling.