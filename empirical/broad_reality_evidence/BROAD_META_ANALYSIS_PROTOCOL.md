# Broad real-world evidence: meta-analysis design (finalized)

## Finalized decision

The broad-evidence meta-analysis has two **primary products** and one **deferred
layer**. This is not a temporary state waiting for more data; it is the design
that the fixed corpus can actually support.

```text
PRIMARY   1. direction map          source-adjudicated sign compatibility per channel   (Layer 3)
PRIMARY   2. yield meta-analysis     how often shallow candidates are direct-route studies (Layer 2)
DEFERRED  3. pooled effect sizes     random-effects magnitude synthesis                  (future Layer 4)
```

The pooled effect-size meta-analysis is **not** the headline result. It is gated
behind primary-source recovery of the Layer 4 exact-stratum anchors and remains
empty until those sources yield correctly oriented numerical contrasts. Forcing
a pooled `k` out of the current corpus is explicitly out of scope.

Why: in the fixed corpus (`FIXED_CORPUS_CAPACITY_V1.md`) the funnel collapses
from 17,933 Crossref candidates to 13 source-adjudicated direction anchors, 5
exact-stratum matches, and **0** primary-source-confirmed numeric effects. No
stratum currently meets even the exploratory `k >= 3` pooling threshold. The
honest deliverable is therefore a map of *sign* and *coverage*, not a pooled
magnitude.

The layered rationale is specified in `HIERARCHICAL_EVIDENCE_SYNTHESIS_PROTOCOL_v1.md`,
which this document does not override. The route-specific full-text extraction
machinery that will eventually populate the deferred layer is specified in
`FLORAL_TRAIT_ANIMAL_RESPONSE_META_PROTOCOL_v1.md`; it is future-layer tooling,
not the current primary analysis.

## Position in the research program

```text
Part I   attraction--defence regime mathematics and sensitivity map (primary inferential engine)
Part II  broad L1/L2 evidence: direction map + yield meta-analysis    (this document)
Part III route-specific effect-size extraction for the deferred pooled layer
Part IV  direct floral-defence field panels
```

Part II does **not** estimate universal biological coefficients for Part I. It
evaluates whether real-world studies are directionally compatible with the
channel assumptions, and how resolvable the evidence base is, where both change
with trait class, outcome, study design, and context.

## Four direct channels

| Route | Question | Expected sign | Part I parameter |
|---|---|---|---|
| `A_to_pollination` | does greater declared attraction associate with greater pollination? | positive | `b_A` |
| `A_to_antagonism` | does greater declared attraction associate with greater floral antagonism? | positive | `d_A` |
| `B_to_antagonism` | does greater declared flower barrier associate with less floral antagonism? | negative | `e_F` |
| `B_to_pollination` | does greater declared flower barrier associate with less pollination? | negative | `c_D` |

These are channel assumptions, not universal claims. A contrary sign is a
potential trait-role, context, measurement, or regime boundary; it is never
silently recoded or discarded.

## Primary product 1 — direction map (Layer 3)

Each genuinely independent study cluster contributes one primary direction record
per route/trait-class/outcome-class/design-class cell:

```text
positive   negative   mixed   null   not_reported
```

The map reports cluster-level counts and the fraction of evaluable signs that
match the declared channel expectation. Sign counts are never treated as causal
effect estimates and are never weighted by citation count or metadata rank.

```text
< 3 evaluable independent clusters  -> insufficient_directional_clusters
>= 3 and >= 80% compatible signs    -> mostly_compatible_with_channel_assumption
>= 3 and <= 20% compatible signs    -> mostly_contradictory_to_channel_assumption
otherwise                            -> mixed_or_context_dependent
```

Inputs and code:

```text
empirical/broad_reality_evidence/broad_route_records.csv
empirical/broad_reality_evidence/broad_meta_analysis_strata.csv
trait_architecture/broad_meta_analysis.py        (direction_map)
scripts/run_broad_meta_analysis.py
```

Output: `broad_direction_map.csv`.

## Primary product 2 — yield meta-analysis (Layer 2)

The route-stratified priority-leak audit is a **methodological** meta-analysis of
the evidence base, not of biology. For route `r` and screen group `g`:

```text
Y_rg ~ Binomial(n_rg, theta_rg)
theta_rg ~ group-level Beta(alpha_g, beta_g)
```

It quantifies how often a shallow priority candidate resolves to a direct-route
study relative to biological non-priority candidates, and how much of the audited
sample is source-accessible versus unresolved. An observed zero in a sparse audit
cell is a source-access limitation, not a biological null.

Inputs and code:

```text
empirical/broad_reality_evidence/priority_leak_audit/priority_leak_audit_yield_by_route_group_v1.csv
trait_architecture/evidence_yield_meta_analysis.py
scripts/run_l1_l2_evidence_yield_meta.py
```

This layer is a calibration and sensitivity analysis. Equal-yield projections are
sensitivity summaries, never confirmed study counts, and the audit sample is a
deterministic route-stratified cohort, not a corpus-wide prevalence estimate.

## Deferred layer — pooled effect sizes (future Layer 4)

Numerical pooling would be allowed only inside a predeclared stratum with the
same route, trait class, outcome class, effect metric, and design class, with
every effect oriented so that positive means *more declared trait/barrier, more
declared outcome*. Supported metrics and recovery methods already exist in
`trait_architecture/broad_meta_analysis.py` and are exercised by
`tests/test_broad_meta_analysis.py`.

The gate:

```text
k < 3 independent clusters  -> no pooled estimate; report effects and gap only
k >= 3                       -> exploratory DerSimonian-Laird random-effects estimate
k >= 5                       -> stability-eligible random-effects estimate
```

Current state: `broad_effect_extractions.csv` is empty of eligible effects and
every stratum is `insufficient_independent_clusters`. This layer stays deferred
until the five Layer 4 anchors in
`meta_analysis_intake/CORE_NUMERIC_EXTRACTION_QUEUE_v1.csv` are resolved to
primary-source numerical contrasts. Even then the first result is effect-level
foundation data and single-study estimates, not a pooled average.

## Explicit prohibitions

```text
- Do not present a pooled effect size as the primary broad-evidence result.
- Do not pool signs as effect sizes.
- Do not pool different trait classes merely because both are called "attraction" or "defence".
- Do not pool visitation, pollen transfer, fruit set, and seed set.
- Do not treat multiple outcomes from a shared panel as independent without a declared multivariate model.
- Do not invert a contrary effect to force agreement with the model.
- Do not call a broad direction map or a yield meta-analysis a direct D1/D2 test.
- Do not expand L1/L2 discovery in order to manufacture a poolable k.
```

## Primary outputs

```text
broad_direction_map.csv                    (primary 1)
priority_leak_audit yield summaries         (primary 2)
broad_meta_analysis_summary.csv             (deferred layer readiness, currently all insufficient)
broad_meta_analysis_effects_used.csv        (deferred layer, currently empty)
broad_meta_analysis_diagnostics.json
```

The key empirical result is a structured map of directional support,
contradiction, heterogeneity, and missingness across the four channels, together
with a calibrated statement of how resolvable the evidence base is — not a single
global mean effect.
