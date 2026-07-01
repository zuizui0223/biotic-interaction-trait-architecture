# B-to-P precision batch 1: abstract-level adjudication

## Frozen source receipt

```text
workflow run: 28497428720
artifact:     8001540786
artifact digest: sha256:8c12af23a803f583e36b4724fe9b061a72a1a81e857cc1285f90077392baf3aa
precision candidates: 638 unique records
B-and-P signal queue: 21 candidates
Crossref deposited abstracts: 14 available, 7 unavailable
```

The B/P signal queue is a revised source-screening order. It was introduced
because the original rank-only B-to-P queue was dominated by floral morphology,
rewards, community ecology, and floral scent studies that did not establish a
barrier role.

## Candidate-level outcome

```text
included_for_source_coding:  4
excluded:                  11
unassessed:                 6
```

Exclusions are not deletions. They remain in
`B_TO_P_BATCH_1_SOURCE_SCREENING.csv` with an explicit reason.

The principal exclusion pattern is informative:

```text
floral reward / attraction / stress response, not independent B: 8
review or framework:                                          3
computational tool, not a primary empirical study:             1
```

No-abstract candidates remain `unassessed`; their titles are not treated as
scientific evidence of a floral barrier role.

## Direct route records at abstract resolution

```text
B_to_pollination: 3
B_to_antagonism:  1
numerical effects: 0
```

### Direct B-to-P evidence

| Study system | Flower barrier | Pollinator outcome | Direction | Qualification |
|---|---|---|---|---|
| *Gelsemium sempervirens* | defensive nectar alkaloid | captive bumblebee behavioral response | negative | magnitude depends on alternative-flower context |
| nectar-feeding birds | nicotine in artificial nectar | feeding frequency and duration | negative | species and sucrose concentration modify tolerance |
| *Delphinium barbeyi* | nectar norditerpene alkaloids | bumblebee visits and time per flower | mixed | high concentrations reduce activity; natural-range treatments show no detected cost |

The `Petunia x hybrida` transgenic floral-volatile experiment is a direct
`B_to_antagonism` record because defensive scent components reduced florivory.
It is **not** assigned B-to-P because its deposited abstract contains no
pollinator response.

## Main scientific result of the precision expansion

The missing B-to-P channel is not empty. At abstract resolution, the clearest
available evidence is a conditional cost of flower defensive chemistry to
pollinator foraging or visitation:

```text
higher defensive nectar alkaloid concentration
    -> lower pollinator visitation / preference / feeding
```

However, this is not a single universal effect:

```text
context of alternative flowers matters
pollinator taxon and diet matter
dose relative to natural nectar matters
controlled feeder assays are not automatically equivalent to intact-flower visitation
```

This pattern is consistent with the negative `B_to_pollination` channel assumed
in Part I, while also demonstrating why Part I must retain context-dependent
parameter scenarios rather than adopt a single empirical coefficient.

## What remains unclaimed

```text
- no pooled B-to-P effect size
- no natural-concentration general estimate
- no direct D1/D2 panel
- no raw parameter calibration for c_D
```

All retained records are `abstract_only`. Full text or public data is needed to
recover metric type, sample sizes, uncertainty, and independent-study details
before any compatible mini-meta-analysis.