# Registered broad direction evidence v1

## Purpose

`broad_route_records.csv` is the live, analysis-facing registry of source-coded
direct-route records. This snapshot promotes only records that have passed a
frozen source-screening batch and a route/role adjudication. It does not promote
all retrieved candidates, and it does not create numerical effects.

## Provenance included in v1

| Source batch | Frozen receipt | Registered record IDs | Resolution |
|---|---|---|---|
| Broad calibration batch 1 | Crossref workflow 28495603975, artifact 8000888585 | `CB1_R001`–`CB1_R008` | Crossref deposited abstract |
| B-to-P precision batch 1 | B-to-P workflow 28497428720, artifact 8001540786 | `BPP1_R001`–`BPP1_R004` | Crossref deposited abstract |

The strict public repository audit for `BPP1_R001`–`BPP1_R004` is recorded in
`precision_expansions/source_audits/B_TO_P_BATCH_1_PUBLIC_SOURCE_AUDIT.md`.
It recovered no eligible DataCite, Dryad, or Zenodo file manifest, so these
records remain direction-only.

## Registered count

```text
records: 12
A_to_pollination: 5
A_to_antagonism: 1
B_to_antagonism: 3
B_to_pollination: 3
```

## What the live direction map can say now

The records occupy 10 exact route × trait-class × outcome-class × design-class
strata. The largest is the manipulated chemical-barrier → pollinator-foraging
stratum with two independent clusters. Every stratum remains below the
predeclared three-cluster minimum for a pooled random-effects estimate.

```text
direction map: yes
quantitative effect extraction: no
random-effects pooled effect: no
Part I numerical calibration: no
```

## Scope boundary

These rows are not a representative sample of the full broad corpus and cannot
be used to estimate corpus-wide sign frequencies. They are an auditable first
registered evidence slice, created from two predeclared calibration batches.
Further batches are appended only after their source-screening decision, route
record, and study-cluster rule are frozen.