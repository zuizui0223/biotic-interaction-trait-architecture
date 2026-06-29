# Matched-study protocol for floral regime evidence

## Why the route changes here

The public global-join route has been assessed and retired for the first
empirical test:

```text
Web of Life × BIEN leaf traits  → insufficient provider-row coverage
GloBI plant–antagonist claims   → not a sampled-network backbone
TRY custom export               → not a reproducible active dependency
```

The replacement is a different evidential design: **studies are the unit of
integration**. A study must record traits and interaction channels in a declared
biological context. It may then contribute one channel, an aligned panel, or a
directly identifiable part of the Part I model.

## Link to Part I

The current score has the exact local mixed partial

\[
\frac{\partial^2 W}{\partial A\,\partial D}
=
H d_A e_F
-
P b_A c_D e^{-c_DD}(1-c_RR)
-
c_{AD}.
\]

The empirical target is therefore **not** a generic correlation between two
traits. It is a declared map from floral traits to pollination, floral
antagonism, and—where available—total reproductive fitness.

The four directional paths in the score are:

```text
A_flower → pollination            b_A
A_flower → floral antagonism      d_A
B_flower → floral antagonism      e_F
B_flower → pollination            c_D
```

A separately observed allocation or fitness layer is needed to resolve the
shared `A_flower × B_flower` cost term `c_AD`.

## Evidence products and permitted claims

| Product | Minimum matched information | Permitted output |
|---|---|---|
| **M0: candidate card** | bibliographic record plus explicit reason it may contain flower traits, pollination, and floral antagonism | search/acquisition priority only |
| **M1: channel ledger** | a direct floral trait plus either pollination or floral-antagonist observation, with site/study identity | one-channel mechanism evidence |
| **M2: aligned two-channel panel** | A/B traits plus pollination and floral-antagonist observations in the same study landscape and overlapping time, but one or more directional paths are unestimated | aligned component panel; no Part I curvature claim |
| **D1: channel-mechanism panel** | M2 plus estimable `A→P`, `A→H`, `B→H`, and `B→P` effects in a declared unit/context | identify the two interaction-channel terms conditional on an observation model; total sign remains unresolved without fitness/cost |
| **D2: observed fitness-surface panel** | D1 plus reproductive-fitness response and denominator on the linked unit | estimate conditional observed A×B fitness curvature; compatible/contradictory/not-identified for a declared scenario, not causal adaptation by default |
| **D3: parameterized score panel** | D2 plus independent shared-cost/allocation evidence or explicit validated calibration | compare the full empirical parameterization with the Part I expression |

A paper title, review statement, or datasets joined only by taxon name never
exceeds M0.

## Non-negotiable matching rules

Every D1+ candidate must document the following baseline structure:

```text
1. Floral attraction trait(s)
   e.g. display, flower/capitulum size, floral scent, reward, colour contrast,
   orientation, access geometry.

2. Floral barrier/resistance trait(s)
   e.g. floral chemical defence, structural protection, trichomes/spines,
   toughness, access limitation, or another separately justified flower-specific
   barrier mechanism.

3. Module separation
   A_flower and B_flower are independently measured. A single composite that
   combines display/access and protection cannot test A_flower × B_flower.

4. Pollination response and denominator
   e.g. standardised visitation, pollen transfer, pollinator effectiveness,
   outcrossing proxy, or reproductive response tied to visitation.

5. Floral-antagonist response and denominator
   e.g. florivory, flower damage, seed predation, nectar robbery, pollen theft,
   or another flower-attacking antagonist.

6. Alignment and linkage
   exact or predeclared-overlap site/time alignment; individual, plant-population,
   patch, or network linkage is declared and never silently upgraded.

7. Recoverability
   raw/machine-readable table, supplement, repository data, or clearly defined
   aggregate. Narrative claims alone do not qualify.
```

D1 adds direct estimation or manipulation evidence for all four arrows:

```text
A_flower → pollination
A_flower → floral antagonism
B_flower → floral antagonism
B_flower → pollination
```

D2 adds a total reproductive-fitness response, for example viable seeds per
marked flower/plant, fruit set with a declared flower denominator, or a
predeclared lifetime-fitness proxy. D3 additionally resolves shared cost by an
allocation measure or transparent calibration.

## What belongs outside this route

- leaf traits and leaf herbivory without a stated cross-organ bridge;
- broad pollination syndromes, because they encode the process being explained;
- interaction claims pooled across studies without study-specific sampling;
- floral traits and florivory measured in different years/sites without a
  declared alignment model;
- global taxon joins using trait imputations as though they were observations;
- studies that call a trait defensive but do not estimate its effect on floral
  antagonism or pollination.

## Study-card workflow

1. Register an M0 candidate through a reproducible seed query, citation chase,
   repository search, or known study.
2. Read full text and supplement before assigning any channel status.
3. Record trait definitions, whether A and B are independently measured,
   response denominators, linkage, site, time, raw-table status, and the status
   of each of the four directional arrows.
4. Record whether total reproductive fitness is observed and whether shared cost
   is measured, calibrated, or unresolved.
5. Run `examples/audit_matched_flower_studies.py`.
6. Acquire data in this order:

   ```text
   supplement / repository
   → machine-readable appendix
   → author-provided table
   → aggregate figure digitisation (M1/M2 descriptive use only)
   → exclude
   ```

7. Freeze the registry before modelling. Do not add studies after seeing a
   pooled sign unless they arise from the predeclared search/citation route.

## Search priority

Prioritise studies in this order:

```text
A. factorial or quasi-factorial A/B manipulation with reproductive fitness
B. individual-level A/B traits + both channels + viable seed/fruit response
C. studies estimating all four directional paths in one matched panel
D. aligned trait/pollination/florivory panels missing one or more arrows
E. one-channel floral mechanism studies
```

A candidate is high-information when metadata/full text indicates at least one
of: trait table, visitor counts, floral-damage counts, seed-predation counts,
individual/plant identifiers, a stated site-period, total fitness, or an
accessible supplement/repository.

After each 15-card block:

- **>= 2 D1–D3 cards:** expand that route and retrieve tables;
- **1 D1–D3 card:** retain as the primary route and citation-chase;
- **>= 3 M2 cards:** retain as a mechanism panel route; do not claim curvature;
- **>= 3 M1 cards:** retain as a descriptive mechanism ledger;
- **0 useful cards:** stop that route.

## Interpretation categories

A D2 or D3 result may be labelled only as:

```text
compatible_with_declared_scenario
contradicts_declared_scenario
not_identified
```

D1 identifies channel balance, not the total Part I sign. `not_identified` is
the correct result whenever an arrow, fitness response, module separation,
denominator, alignment, linkage, or recoverable table is absent. It is not
evidence for absence of a floral trade-off or complementarity.
