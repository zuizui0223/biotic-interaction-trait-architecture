# Protocol: all-258 evidence-architecture audit

## Question

The fixed 258-work corpus is not an effect-size meta-analysis corpus. Its
question is instead:

> Within a reproducibly retrieved floral mutualist–antagonist literature corpus,
> how often are attraction, flower-specific barrier traits, pollination,
> floral antagonism, and reproductive fitness measured together in a design that
> could identify the project’s four paths?

This is a **study-design and identifiability audit**. It tests the measurement
architecture of the literature, not the universal sign or magnitude of a
biological trait effect.

## Scope

```text
retrieval unit:      258 fixed OpenAlex candidate works from PR #20
analysis unit:       one candidate work after DOI/title duplicate audit
current DOI state:   256 rows have a DOI; 2 rows do not
candidate status:    M0 discovery context unless a higher evidence status is
                     independently established elsewhere
```

The corpus was retrieved with floral-interaction seed routes. It is therefore
not a random sample of all plant ecology or all pollination papers. Results are
reported as properties of this fixed retrieval corpus, never as field-wide
prevalence estimates.

## Why all 258 rows are useful

Every candidate contributes one observation about whether a study design makes
one or more required components observable. A paper does **not** need to expose
an eligible effect coefficient to contribute to this audit.

```text
eligible registry effect       -> evidence about a specific path
accessible but blocked paper   -> evidence about a missing design component
review/context paper           -> evidence about conceptual versus measured coverage
inaccessible paper             -> evidence about public reproducibility constraints
metadata-only paper            -> retained as unknown, never converted to absence
```

Thus a result such as "many studies mention pollination but few directly measure
a flower-specific barrier and floral antagonism on a shared unit" is a
substantive result about knowledge architecture, even though it is not a
biological parameter estimate.

## Two-layer coding design

The fixed matrix separates retrieval metadata from source-verified coding.

### Layer 0: fixed retrieval metadata

All 258 rows contain the archived OpenAlex attributes:

```text
work type, year, DOI state, OA route, abstract availability, citation count,
seed route, and four metadata signals (A, B, P, H)
```

These signals are **retrieval cues only**. They may arise from title/abstract
language, search-route logic, or conceptual discussion. They are never treated
as proof that a study measured the relevant variable.

### Layer 1: evidence-architecture coding

Each candidate is coded from the strongest source actually inspected:

```text
A_flower_status     direct floral attraction/display trait
B_flower_status     flower-specific barrier/access/resistance trait
P_status            pollination outcome
H_status            floral antagonism outcome
W_status            reproductive-fitness outcome
shared_biological_unit_status
trait_outcome_effect_status
denominator_or_exposure_status
causal_design_status
public_data_status
max_evidence_level
```

Allowed component statuses are:

```text
unassessed
not_stated
mentioned_not_measured
measured_indirect
measured_direct
```

`unassessed` is not zero. It means the relevant source has not been reviewed.
A missing abstract, inaccessible full text, or unresolved source relation is
coded as `unassessed` or `not_stated` only when that distinction is warranted by
the source basis.

## Design endpoint

For each fully coded work, calculate a descriptive architecture vector:

```text
(A, B, P, H, W)
```

where a component is present only at `measured_direct`. Then report:

1. the frequency of all observed vectors;
2. the distribution of 0–5 directly measured components;
3. the fraction with a shared biological unit;
4. the fraction that can, in principle, support each of the four paths;
5. the fraction that reaches M1, M2, D1, D2, or D3 under the existing matched
   study protocol;
6. the source/reproducibility bottleneck at which otherwise informative studies
   stop.

The primary endpoint is **four-path identifiability**, not effect direction.

## Permitted quantitative comparisons

After source-verified coding is complete, the following are permitted within the
fixed corpus:

```text
- exact counts and confidence intervals for design-component coverage;
- stratified summaries by publication period, work type, seed route, and source access;
- a permutation test of observed co-measurement architecture against a null that
  preserves each component's marginal frequency across works;
- regression of an identified design endpoint (for example, shared-unit or D1
  readiness) on prespecified bibliographic/design descriptors.
```

Any model is descriptive of the retrieved corpus. It does not estimate floral
trait selection, path coefficients, or a universal ecological trade-off.

## Validation and adjudication

```text
1. Code all 235 candidates with archived abstracts first.
2. Keep the 23 no-abstract candidates explicitly metadata-only.
3. Review full text only for candidates whose abstract coding could plausibly
   change an M1/M2/D1 boundary.
4. Independently recode a stratified validation set: all high-information
   candidates plus a reproducible random sample from every retrieval-signal
   vector and work-type stratum.
5. Record disagreements and adjudication reasons in the coding note.
```

A full-text result overrides abstract coding. A verified data table overrides
textual implication about a denominator, shared unit, or direct effect.

## Explicit prohibitions

```text
- Do not average metadata signal flags as biological effect directions.
- Do not treat title/abstract mentions as measured A, B, P, H, or W components.
- Do not call a study D1/D2/D3 because its title contains all relevant words.
- Do not count multiple papers from one observation panel as independent
  biological replication in the effect registry.
- Do not infer global literature prevalence beyond this fixed retrieval corpus.
```

## Relationship to the four-path effect registry

```text
all-258 audit  = asks whether the literature has the architecture needed to test
                  the theory
four-path registry = extracts compatible quantitative effects where source,
                     unit, denominator, uncertainty, and role gates are passed
```

The two outputs answer different questions and must remain separate.