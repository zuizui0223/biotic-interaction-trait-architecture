# Hierarchical evidence synthesis protocol v1

## Question

How can the entire broad literature corpus be used without pretending that every retrieved article is a directly measured, independent causal effect?

The answer is to retain every layer for the question it can actually answer.

```text
Layer 1  discovery universe
Layer 2  metadata triage + audit calibration
Layer 3  source-adjudicated route and direction map
Layer 4  compatible quantitative effect extraction
Layer 5  route-specific full-text resolution
```

No layer is discarded merely because it cannot enter a conventional meta-analysis.

## Layer 1 — Discovery universe

**Input:** every deduplicated Crossref candidate returned by the frozen query registry.

**Use:** map query coverage, route-family membership, publication characteristics, metadata-signal overlap, and the amount of high-recall retrieval noise.

**Cannot support:** a claim that a trait was measured, a route exists, a result has a sign, or a paper supplies an effect size.

## Layer 2 — Metadata triage and audit calibration

**Input:** screened candidate table and the route-stratified priority-leak audit.

**Use:** show how the priority queue behaves relative to biological non-priority candidates in the sampled audit cohort; quantify audited, screenable, direct-route, and unresolved rows by route.

**Cannot support:** a corpus-wide prevalence estimate. The audit queue is a deterministic, route-stratified sample, and rows without an accessible abstract remain unresolved rather than absent.

## Layer 3 — Source-adjudicated direction map

**Input:** `broad_route_records.csv`.

**Use:** compare where source-confirmed evidence sits across route, B/A trait class, outcome layer, design class, and direction (`negative`, `mixed`, `positive`, or `null`). This is where condition dependence becomes visible without pooling incompatible outcomes.

**Cannot support:** a common numerical magnitude unless the source contains compatible quantitative information.

## Layer 4 — Quantitative effects

**Input:** `broad_effect_extractions.csv`.

**Use:** conduct a route- and outcome-specific synthesis only after verifying effect orientation, exposure denominator, independent panel identity, variance/raw fields, and a source locator.

**Guardrails:**

- Do not turn an abstract into an effect size.
- Do not count dose treatments, species, time points, or response variables as independent studies before checking shared panels.
- Do not pool foraging/preference with flower visitation, pollen transfer, or fitness.
- Do not average natural-range and supra-natural treatment levels.

## Layer 5 — B-to-P full-text resolution

**Input:** `precision_expansions/fulltext/B_TO_P_FULLTEXT_READING_QUEUE_v1.csv`.

**Use:** resolve the direct B-to-P anchors at full-text level. This layer is deliberately small because it is not a discovery corpus; it asks whether already identified study clusters provide a comparable numerical contrast.

## Analysis outputs

The workflow writes a report with four artifacts:

```text
artifacts/hierarchical_evidence_synthesis/
  evidence_layers_by_route.csv
  source_adjudicated_direction_cells.csv
  hierarchical_evidence_summary.json
  HIERARCHICAL_EVIDENCE_SYNTHESIS.md
```

## Paper-level interpretation

The manuscript should integrate these layers in order:

1. the literature is structurally uneven across pathways and outcome types;
2. screen calibration defines which parts of the retrieval are resolved versus still unavailable;
3. source-adjudicated studies identify route signs and ecological contingencies;
4. only a narrow compatible subset can estimate magnitude; and
5. those contingencies determine which theoretical complement/substitute regimes remain plausible.

A sparse quantitative stratum is therefore not a failed meta-analysis. It is a documented empirical boundary on the claims that can be parameterized.
