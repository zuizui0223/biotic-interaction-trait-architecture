# Primary broad-evidence figures

Two figures for the finalized primary products (`BROAD_META_ANALYSIS_PROTOCOL.md`).
Both are dependency-free SVG, regenerated from committed inputs only.

## Reproduce

```bash
python scripts/plot_broad_evidence_primary_figures.py \
  empirical/broad_reality_evidence/broad_route_records.csv \
  empirical/broad_reality_evidence/priority_leak_audit/priority_leak_audit_yield_by_route_group_v1.csv \
  empirical/broad_reality_evidence/figures
```

## `fig1_direction_map.svg` — primary product 1

Per-channel sign compatibility of the source-adjudicated direction anchors. Bar
length is the number of independent study clusters (not an effect size); colour is
agreement with each channel's model-expected sign. A sign is only "read" where a
route×trait×outcome×design cell reaches k≥3 clusters — currently one cell
(B→pollinator, chemical barrier, manipulation). The B channels carry consistent
compatible (defensive) signs; the A channels are mostly mixed/context-dependent
and A→antagonist is essentially uncharacterised (n=1).

## `fig2_yield_meta_analysis.svg` — primary product 2

Left: direct-route evidence yield by screen group (priority vs biological
non-priority). Right: the priority-vs-non-priority enrichment odds ratio per route
with 95% CI and the random-effects pooled estimate (OR 1.47, 95% CI [0.35, 6.12]).
The pooled interval crosses 1: the priority screen shows only weak, non-significant
enrichment. This is a methodological audit meta-analysis, not a biological effect.

## Note

The SVGs render on a light surface with a CVD-validated palette. Category
identity is carried by both colour and direct labels, so the figures remain
readable without colour.
