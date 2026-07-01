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
| B-to-P precision batch 2 | Crossref workflow 28500362434, artifact 8002716214 | `BPP2_R001` | Crossref deposited abstract |

The strict public repository audits for the precision records are recorded in:

```text
precision_expansions/source_audits/B_TO_P_BATCH_1_PUBLIC_SOURCE_AUDIT.md
precision_expansions/source_audits/B_TO_P_BATCH_2_PUBLIC_SOURCE_AUDIT.md
```

Neither audit recovered an eligible DataCite, Dryad, or Zenodo file manifest,
so the precision records remain direction-only.

## Registered count

```text
records: 13
A_to_pollination: 5
A_to_antagonism: 1
B_to_antagonism: 3
B_to_pollination: 4
```

## What the live direction map can say now

The records occupy 10 exact route × trait-class × outcome-class × design-class
strata. One stratum now reaches the three-independent-cluster minimum for a
directional conclusion:

```text
B_to_pollination × chemical_barrier × pollinator_preference_or_foraging × manipulation

independent clusters: 3
negative directions:  3
positive directions:  0
map status:           mostly_compatible_with_channel_assumption
```

The three systems are defensive nectar alkaloids in *Gelsemium*, nicotine in
artificial nectar offered to birds, and zygacine in pollen/nectar of
*Toxicoscordion*. Their convergence supports the **direction** predicted by the
B→P channel in this restricted foraging/choice stratum. It does not establish a
universal sign across pollinator taxa, doses, or intact-flower visitation.

All other strata remain under the three-cluster threshold. None of the 13
records has a compatible numerical estimate plus uncertainty, so the
quantitative pipeline remains empty:

```text
direction map: yes
quantitative effect extraction: no
random-effects pooled effect: no
Part I numerical calibration: no
```

## Scope boundary

These rows are not a representative sample of the full broad corpus and cannot
be used to estimate corpus-wide sign frequencies. They are an auditable first
registered evidence slice, created from predeclared calibration batches.
Further batches are appended only after their source-screening decision, route
record, and study-cluster rule are frozen.