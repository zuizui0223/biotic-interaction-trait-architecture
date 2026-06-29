# Reassessment: what the Part I score requires from an empirical study

## Decision

The matched-study route remains the right replacement for unmatched global joins,
but the earlier D1 rule was **necessary and not sufficient** for the current
mathematical claim.

A table that contains `A_flower`, `B_flower`, pollination, and floral antagonism
in the same context is valuable. By itself, however, it cannot identify the sign
of the Part I mixed partial:

\[
\frac{\partial^2 W}{\partial A\,\partial D}
=
H d_A e_F
-
P b_A c_D e^{-c_DD}(1-c_RR)
-
c_{AD}.
\]

The equation is a statement about **local curvature of a fitness score**, not a
claim that natural populations must display positive or negative trait
covariance.

## Why the original matched-panel rule was insufficient

The old structural D1 rule required independently measured A and B traits plus
both interaction channels, alignment, denominators, and a recoverable table.
That establishes an unusually useful *joint panel*, but it does not by itself
establish the four directional links in the equation:

```text
A → pollination        b_A
A → floral antagonism  d_A
D → floral antagonism  e_F
D → pollination        c_D
```

Nor does it identify the residual shared investment term `c_AD`.

For example, a study may measure floral chemical concentration, visitor counts,
and florivory. It cannot inform the pollination-obstruction term unless the
chemical trait's own effect on pollination is estimated. Likewise, observed
florivory is not evidence that attraction increases florivory; that requires an
estimated A → antagonist path.

## Revised evidence ladder

The project now distinguishes structural matching from mathematical
identifiability.

| Level | Minimum empirical content | Mathematical claim permitted |
|---|---|---|
| **M0** | discovery record only | none |
| **M1** | one direct trait–channel link | one-channel mechanism description |
| **M2** | matched A/B traits plus pollination and antagonist observations, but one or more directional paths are not estimated | aligned component panel; no Part I curvature claim |
| **D1: channel-mechanism panel** | M2 plus estimable `A→P`, `A→H`, `D→H`, and `D→P` paths in the declared unit/context | identify the two biological channel terms, conditional on the observation model; the total sign remains unresolved without fitness/cost information |
| **D2: observed fitness-surface panel** | D1 plus an individual- or declared aggregate-level total reproductive-fitness response with a denominator | estimate an observed conditional A×D fitness curvature and compare it with a declared Part I scenario; this is not causal adaptation without an intervention/identification design |
| **D3: parameterized score panel** | D2 plus an independent allocation/shared-cost measurement, or a transparent calibrated model that identifies the residual `c_AD` term | compare the full empirical parameterization with the exact Part I expression |

No level is automatically a proof of adaptive evolution.

## The empirical target is an effect map, not a trait correlation

### Channel 1: pollination/access

For a direct floral trait `A` and barrier/access-limitation trait `D`, the
model's pollination component is

\[
Y_P = P\,(b_0+b_A A)\,e^{-c_DD}(1-c_RR).
\]

A compatible observation model must estimate, or experimentally identify:

```text
A → pollination outcome        sign and scale of b_A
D → pollination outcome        sign and scale of c_D
```

Visitor count can be a response only when its sampling denominator and its
relationship to service are declared. Pollen transfer, outcrossing, fruit set,
or viable seed set may be closer responses, but they still require an explicit
link to the chosen score component.

### Channel 2: floral antagonism

The model's floral-damage component is

\[
Y_H = H\,(f_0+d_A A)(1-e_FD).
\]

A compatible observation model must estimate, or experimentally identify:

```text
A → floral-antagonist exposure     sign and scale of d_A
D → floral-antagonist reduction    sign and scale of e_F
```

Damage incidence, seeds consumed, or floral-tissue loss must carry a stated
at-risk denominator. Antagonism against leaves, stems, or unrelated reproductive
stages is not a substitute without a declared biological bridge.

### Total-score layer

The shared-cost term is not a floral interaction observation:

\[
-c_{AD} A D.
\]

It is an allocation/fitness penalty. Therefore the exact total sign cannot be
identified from pollination and florivory channels alone. There are two valid
routes:

1. fit an observed reproductive-fitness surface `W(A,D)` with the contextual
   channel variables, treating unobserved cost as residual curvature; or
2. obtain an independent allocation/cost measure and fit the parameterized score
   explicitly.

The first route qualifies for D2, the second for D3.

## Consequence for study screening

A high-information candidate is now prioritized by this order:

```text
1. factorial or quasi-factorial manipulation of A and D with reproductive fitness
2. natural individual-level A and D variation + both channel outcomes + viable seed/fruit outcome
3. a matched panel that estimates all four directional paths
4. matched panels with traits and outcomes but missing one or more arrows
5. one-channel mechanism studies
```

The following are not promoted merely because they have raw data or use the word
"trade-off":

- a floral trait plus florivory without a measured pollination response;
- a pollination-and-damage panel where D is not independently measured;
- a panel where D is measured but its effect on pollination is untested;
- a panel where total fitness is absent;
- a cross-study or cross-taxon join that has no common plant/site/time unit.

## Implications for current candidates

| Candidate | Current status under the revised ladder | Main gap |
|---|---|---|
| *Tanacetum vulgare* | M1 | pollination response absent |
| *Pedicularis rex* | M2 | A/B composite and no recoverable individual table |
| *Dalechampia scandens* | high-information M2 pending trait-function screen | no demonstrated independent B_flower path yet |
| *Rivea ornata* | high-information M2 | defence mechanism is not an independently measured, plant-level B trait; pollination and florivory pathways are not a common A×B panel |
| *Impatiens capensis* | M0 high priority pending public-table linkage | package declares relevant channels, but ID structure and independent B trait remain unverified |

## Analysis templates

### D1: channel-mechanism model

At an individual `i` in context `s`, fit the four declared paths rather than
pooling traits across contexts:

```text
pollination_i ~ A_i + D_i + controls + context_s
antagonism_i  ~ A_i + D_i + controls + context_s
```

The model family must respect the denominator: binomial for damaged/inspected
flowers or seeds, count model with exposure offset for visits, and an explicit
service proxy for pollination.

### D2: observed fitness surface

When viable seed production or another predeclared reproductive-fitness response
is available, fit a contextual surface such as:

```text
fitness_i ~ A_i * D_i * (P_s + H_s) + R_i + controls + random effects
```

or a nonlinear likelihood derived from the declared channel functions. The target
is the conditional `A:D` curvature, not the raw correlation between A and D.

### D3: parameterized score comparison

Only after an allocation/shared-cost measurement or calibration is justified may
an analysis claim to compare all terms in the exact expression. Otherwise,
`c_AD` remains an explicitly unresolved residual.

## Practical decision

Continue the literature route, but replace the old question

```text
Does this paper have A, B, pollination, and antagonism in one table?
```

with

```text
Which of the four directional paths are estimable?
Does the same unit have a total reproductive-fitness response?
Is shared cost observed, calibrated, or unresolved?
```

This makes the empirical program narrower in claims but broader in useful
outputs: M1 and M2 studies remain genuine mechanism evidence, while D1–D3
identify exactly what is required for a numerical connection to Part I.
