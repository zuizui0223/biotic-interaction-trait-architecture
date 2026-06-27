# Meta-analysis readiness gate for Megachile leaf-material use

## Do not confuse a list of used plants with a preference dataset

A positive-use list alone can describe the traits of plants that have been recorded with leaf-cutting damage. It cannot estimate trait-associated use or preference, because the set of plants that were available but unused is missing.

The target estimand for the primary analysis is therefore conditional use among surveyed or otherwise available plants:

\[
\Pr(Y_{ijs}=1 \mid A_{ijs}=1)
\]

where \(Y_{ijs}\) is direct leaf-material use for plant \(i\), in sampling unit \(j\), from study \(s\), and \(A_{ijs}\) records that the plant was in the study's available/surveyed universe.

## Candidate-dataset eligibility

A source is screened in this order. Failure at any required gate means it is retained only as background or descriptive evidence, not pooled in the primary model.

| Gate | Required for primary meta-analysis? | What is checked |
|---|---:|---|
| direct-use definition | yes | cut leaf/petal, material transport, or nest-cell material; not floral visitation or generic damage |
| identifiable sampling unit | yes | site, site-year, transect, garden, experimental arena, or comparable unit |
| denominator / availability universe | yes | surveyed plant list, experimental offering set, or documented available flora with effort |
| taxonomic resolution | yes | plants resolved to species or resolvable synonyms; bee at least leaf-cutting Megachile guild |
| extractable response | yes | use/non-use, count plus effort, or a recoverable table/supplement/raw data |
| effort metadata | yes | search time, number of plants examined, sampling dates, or experimental replication |
| independent unit count | yes | recoverable site/arena/time units; not merely multiple species from one anecdotal observation |
| trait join feasibility | yes | at least one prespecified trait source can be joined to most plants |
| licensing / provenance | yes | citable source and recoverable locator for every extracted row |

## Accumulation targets

These are internal go/no-go targets, not universal publication rules.

### Stage 0 — feasibility

Proceed with extraction development only after at least **three** eligible sources, each with a genuine availability denominator, are found.

### Stage 1 — pilot hierarchical analysis

Run only as a sensitivity/pilot analysis after all are met:

```text
>= 8 eligible independent datasets or site-year/arena datasets
>= 200 plant-by-unit rows with explicit use/non-use or count + effort
>= 100 unique plant species after synonym reconciliation
>= 30 unused-but-available plant species across the pooled data
no single study contributes > 35% of rows
>= 70% of used and available plant taxa join to at least one core trait source
```

### Stage 2 — main comparative analysis

Promote to the main empirical chapter only after all are met:

```text
>= 15 independent datasets or site-year/arena datasets
>= 500 plant-by-unit rows
>= 200 unique plant species
>= 3 biogeographic regions or clearly separated habitat systems
>= 50 unused-but-available plant species per broad region where possible
no single study contributes > 25% of rows
leave-one-study-out trait-effect direction is stable for the core trait set
```

If Stage 2 is not reached but Stage 1 is reached, label the output explicitly as a pilot synthesis and use it to choose the next standardized field protocol.

## Adaptive source strategy

### Route A: published surveys and experiments

This is the highest-value route because it can carry the denominator. Search for studies using combinations of:

```text
Megachile / leafcutter bee / leaf-cutting bee
plant choice / nesting material / leaf material / nest material
survey / experiment / offered plants / available plants / transect / damage
```

A study with only a positive host list does not count toward Stage 0.

### Route B: recoverable study supplements and author data

For an otherwise eligible paper lacking a visible table:

1. inspect supplement and repository links;
2. inspect cited data repositories;
3. request a citable data table from authors only after a paper passes all other gates.

### Route C: standardized field or common-garden data

If Route A cannot pass Stage 0 after a fixed screening batch, pivot rather than endlessly collecting anecdotal records. The fallback design is a repeated offered-leaf/sentinel-plant protocol or common-garden plant panel with trap nests and replicated sites. This directly supplies availability, effort, and non-use rows.

## Fixed iteration rule

Work in rounds of ten candidate studies/sources.

For each round report:

\[
R_{\rm eligible}=\frac{n_{\rm primary\ eligible}}{n_{\rm screened}},\quad
R_{\rm denominator}=\frac{n_{\rm availability\ known}}{n_{\rm screened}},\quad
R_{\rm extractable}=\frac{n_{\rm table\ recoverable}}{n_{\rm screened}}.
\]

Decision:

```text
If >= 2 primary-eligible sources occur in a 10-source round:
  continue the same route for another round.

If 0 primary-eligible sources occur in two consecutive rounds:
  stop that route and pivot.

If a route yields positive-use lists but no denominators:
  keep it only for descriptive trait distribution, never for preference inference.

If Routes A and B fail to reach 3 eligible sources after 30 screened sources:
  promote Route C (standardized data collection) to the main plan.
```

## Current status

No candidate source has yet passed the full primary eligibility gate. Previous web observations remain material-mode/context evidence only. The Singapore-style survey claim is **not counted** until its primary source, sampling denominator, and extractable plant-level table have been checked.
