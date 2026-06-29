# Public-data route results — 2026-06-29

## Purpose

These are reproducible **data-route decisions** for Part II. They do not test an
ecological trait effect and do not provide evidence against the Part I model.
They decide whether a proposed public source has the structure required to move
on to an empirical analysis without manual filling or an unmatched database join.

## 1. BIEN leaf-trait provider-row screen

**Question.** Can a script-accessible BIEN source provide a plausible first
leaf-functional-trait receipt for a reproducible, one-plant-per-network sample
from oriented Web of Life pollination networks?

**Run.** GitHub Actions `Probe public trait and antagonist-data gates`, run 4;
30 networks sampled with seed `20260629`; BIEN R package `1.2.8`.

**Result.** The live BIEN catalogue supplied labels for all five requested
functional concepts, but returned provider rows for too few of the sampled taxa:

| Functional concept | Provider rows / 30 sampled taxa | Availability rate |
|---|---:|---:|
| SLA: leaf area per leaf dry mass | 2 | 6.7% |
| LDMC: leaf dry mass per leaf fresh mass | 2 | 6.7% |
| Leaf nitrogen | 1 | 3.3% |
| Leaf phosphorus | 1 | 3.3% |
| Leaf thickness | 1 | 3.3% |

The predeclared advance criterion required at least one construction trait
(SLA, LDMC, or thickness) **and** at least one nutrient trait (N or P) to each
have at least 60% provider-row coverage with zero query errors. The criterion
was not met.

**Decision.** `no_go_BIEN_as_current_automated_leaf_quality_provider` for this
Web of Life-based broad trait route.

**Boundary.** These are provider-row results only. They are not a test of
measurement-level directness, no proof that BIEN lacks all leaf data, and no
claim about leaf traits in nature. The result is sufficient to retire this
specific global join as the active route.

## 2. GloBI antagonist-network contract screen

**Question.** Can GloBI's public interaction API serve as a ready, sampled
plant-antagonist network backbone for an effort-aware cross-study analysis?

**Result.** The API provides interaction claims, taxonomy, some study
provenance, and location/time fields. It does not expose the two non-negotiable
network-contract fields required here:

```text
unique sampled network identifier
sampling effort or observation denominator
```

A non-unique study title is not silently substituted for a network identifier,
and interaction counts/frequencies are not treated as comparable effort.

**Decision.** `no_go_GloBI_as_ready_multiplex_network_backbone`.

**Boundary.** GloBI remains suitable for discovery, provenance tracing, and
locating original studies. It is not pooled as a sampled herbivory network.

## Consequence for Part III

The active empirical route is now the matched floral-study protocol:

```text
same study landscape
+ floral attraction traits
+ floral barrier/resistance traits
+ pollination response
+ floral-antagonist response
+ time/site alignment and linkage unit
+ recoverable table
```

See `empirical/matched_flower_regime/MATCHED_STUDY_PROTOCOL.md`.
