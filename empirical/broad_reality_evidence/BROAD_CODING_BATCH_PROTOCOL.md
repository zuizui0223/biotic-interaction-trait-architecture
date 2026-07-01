# Broad source-coding batch protocol

## Goal

Convert the priority cohort into transparent source-coded route records without
changing definitions after seeing study results.

## Stage 0: frozen retrieval receipt

For any coding campaign, pin:

```text
GitHub Actions artifact digest
query report CSV
priority cohort CSV
source-screening matrix CSV
```

The live Crossref retrieval is never regenerated in the middle of a coding
campaign. A later retrieval is a new receipt, not a replacement for already
coded rows.

## Stage 1: calibration batch

Before bulk coding, select a reproducible calibration batch with representation
from all discovery route families:

```text
A_to_pollination
A_to_antagonism
B_to_antagonism
B_to_pollination
joint_channels
```

The calibration objective is not an early biological conclusion. It is to test
whether the codebook cleanly distinguishes:

```text
- direct floral A versus flower-specific B;
- P versus H versus W outcomes;
- observed sign versus narrative discussion;
- independent study cluster versus multiple analyses from one panel;
- usable quantitative table versus direction-only result.
```

Log every ambiguity and update the codebook once, before bulk coding begins.
No bulk record is recoded merely to increase alignment with Part I.

## Stage 2: candidate-level source screen

For every candidate in the pinned source-screening matrix, record one decision:

```text
included_for_source_coding
excluded
```

Common exclusion reasons:

```text
nonbiological retrieval noise
review or conceptual article
no direct floral trait
no relevant P/H outcome
leaf-only trait or antagonist
duplicate study panel
source inaccessible for the intended resolution
```

An inaccessible source is not treated as evidence of absence.

## Stage 3: route-record coding

Included primary studies create one or more direct route records. Assign one
primary sign record per independent study-cluster stratum. A joint-channel paper
may yield several records only if it directly evaluates several trait–outcome
pairs.

## Stage 4: quantitative extraction

Only after route coding, extract numerical effects for predeclared compatible
strata. Prefer source tables or public data; retain a source locator and exact
orientation. Do not extract every coefficient in a paper.

## Stage 5: locked analysis snapshots

Run the directional map and mini-meta-analysis only after a declared coding
batch is complete. Report:

```text
number screened
number included primary studies
route-record counts
independent cluster counts
quantitative-effect counts
unpooled versus pooled stratum status
```

A new batch creates a new analysis snapshot. Earlier outputs remain auditable.

## Stopping rules

```text
No source screen → no route record.
No direct trait/outcome sign → no directional conclusion.
No uncertainty or reconstructable raw inputs → direction-only, no effect extraction.
Fewer than 3 independent clusters → no pooled mean.
Strong heterogeneity → retain context/design stratification; do not publish a global mean.
```
