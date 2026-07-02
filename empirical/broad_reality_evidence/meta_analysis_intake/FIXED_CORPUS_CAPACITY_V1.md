# Fixed-corpus layer capacity v1

## Fixed-corpus rule

This capacity assessment treats the existing broad-retrieval result as closed for discovery. No additional paper retrieval is required to populate this plan.

The canonical retrieval receipt is:

```text
workflow: Harvest broad reality evidence #40
workflow run: 28569516037
artifact: broad-reality-evidence-corpus
artifact ID: 8030510716
artifact digest: sha256:2323b427ece3a01eec6a313a98b108a505f653245e7d3dc5a282f20d557d5132
retrieval date: 2026-07-02
```

## Counts at each layer

| Layer | Definition | Fixed count | What the count can support |
|---|---|---:|---|
| L1 | Deduplicated Crossref discovery candidates | 17,933 | Research-space coverage and retrieval composition only. |
| L2a | `priority_for_shallow_source_coding` | 1,606 | First source-reading queue; not a route claim. |
| L2b | `biological_context_needs_route_screen` | 3,995 | Contextual hold set; not excluded from biology, but not first-line reading. |
| L2a+L2b | Biological screen-pass universe | 5,601 | Maximum metadata-supported source-screen universe under the fixed corpus. |
| L2 audit | Frozen route-stratified audit rows | 300 | Calibration of the priority screen only. |
| L2 audit | Screenable rows / unresolved rows | 136 / 164 | Shows source-access limitation; unresolved is not route absence. |
| L3 | Source-adjudicated primary direction anchors | 13 | Route, trait, outcome, design, and direction map. |
| L4 | Exact matches to an existing quantitative stratum | 5 | Core primary-source/numeric extraction queue. |
| L4 hold | Direction anchors with no exact current stratum | 8 | Fixed as direction-map evidence; do not widen outcome/design cells post hoc. |
| L5 | Primary-source-confirmed numeric effects | 0 | No current effect-size calculation. |
| Pooling | Strata meeting exploratory `k >= 3` | 0 | No current random-effects synthesis. |

## Core exact-stratum queue

The five exact-cell anchors are committed in `CORE_NUMERIC_EXTRACTION_QUEUE_v1.csv`.

```text
AP_visual_visitation_lrr_observational: 2 direction anchors
AH_visual_damage_logor_observational:   1 direction anchor
BH_chemical_damage_logor_manipulation:  1 direction anchor
BP_chemical_visitation_lrr_manipulation:1 direction anchor
```

All five remain at abstract-only source basis. Their next task is source recovery and one correctly oriented numeric comparison per independent study cluster, not pooling.

## Fixed decisions

1. **Freeze L1/L2 discovery.** The source corpus and screen counts are not expanded in order to manufacture a poolable `k`.
2. **Freeze L3 direction-map-only anchors.** The eight nonmatching records remain in the evidence map and do not enter a new ad hoc stratum.
3. **Prioritize L4 core extraction.** Resolve only the five exact-predeclared records for primary source, comparison definition, independent panel, and uncertainty/raw fields.
4. **Keep L5 empty until justified.** `broad_effect_extractions.csv` receives a row only after all numerical gate requirements are met.
5. **No pool under the current fixed corpus.** If all five effects are recovered, they are effect-level foundation data and single-study estimates; the stratum-specific exploratory threshold remains unmet.

## Consequence

The immediate deliverable is not a forced meta-analysis. It is a durable, auditable numeric foundation that makes the next claim precise:

> In the fixed current corpus, which direct pathway cells have source-located, correctly oriented numerical evidence, and which remain direction-only or structurally unpopulated?
