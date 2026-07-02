# B-to-P full-text extraction protocol v1

## Scope

This is a narrow source-resolution pass over the four already registered direct `B_to_pollination` study clusters. It does not add a retrieval route, enlarge the broad corpus, alter the B definition, or change a recorded direction before source review.

```text
flower-specific chemical barrier
    -> measured pollinator behavior or visitation outcome
```

The four records are carried forward from the existing B-to-P precision batches. Their present direction coding is abstract-based only.

## Why this pass is necessary

The currently registered records differ in all three ways that determine whether numerical synthesis is meaningful:

```text
outcome layer:       foraging/preference versus flower visitation
exposure context:    natural-range status not yet source-adjudicated
experimental unit:   individual consumer response, flower-level visits, or context-specific panels
```

Therefore, no pooled B-to-P estimate is calculated at this stage.

## Source priority order

For every queue item, inspect the first available source in this order and retain a precise locator:

1. publisher full text and supplementary files;
2. author-deposited accepted manuscript or institutional repository copy;
3. article-linked public dataset that passes the existing article-to-dataset identity contract;
4. graphical result only when the source itself reports enough design and axis information for a documented reconstruction.

A search-result snippet, title, abstract, review statement, or an unlinked dataset cannot supply a quantitative field.

## Required full-text fields

For each independent comparison, extract or explicitly mark unavailable:

```text
B treatment and control definition
chemical identity and concentration units
dose relation: natural-range / within-natural-range / supra-natural / unresolved
consumer taxon and specialization status
outcome layer: foraging/preference / visitation / pollen transfer / reproductive outcome
response unit and exposure denominator
experimental unit, replicate number, and shared panel ID
means with SD/SE and n, model coefficient with uncertainty, or count data
source locator: page, table, figure, supplement, or public-data file
```

## Extraction states

```text
FT0_source_unavailable
    no inspectable full text, supplement, manuscript, or identity-linked public data

FT1_direction_only
    source confirms the direct route and sign but cannot support a compatible numerical contrast

FT2_numeric_candidate
    source supplies a contrast, unit, denominator, and uncertainty or raw reconstruction fields;
    effect conversion still requires a separate extraction check

FT3_effect_extracted
    a single primary comparison has been entered into broad_effect_extractions.csv with
    orientation, source locator, and independent panel identity checked
```

## Non-pooling rules

- Do not combine foraging/preference outcomes with flower-visitation outcomes.
- Do not combine natural-range and supra-natural concentrations.
- Do not combine species, sucrose treatments, dose levels, or repeated measures before identifying the independent experimental panel.
- Do not use an induced deterrence response as evidence of pollen transfer or plant reproductive cost unless that outcome was measured.
- Do not create an effect size from a publisher abstract.

## Decision after the four-source pass

A B-to-P numerical synthesis is considered only within one predeclared compatible stratum:

```text
BP_chemical_visitation_lrr_manipulation
BP_physical_visitation_lrr_manipulation
```

A stratum remains non-synthesizable whenever it has no numerically extractable independent comparisons, or whenever available contrasts differ in outcome layer, dose relation, or experimental unit. In that case the result is reported as a structured evidence gap and retained as a mechanism map rather than being forced into a pooled estimate.

## Deliverables

- A fully source-adjudicated version of `B_TO_P_FULLTEXT_READING_QUEUE_v1.csv`.
- Zero or more individually documented effect extractions.
- A short readiness report stating which outcome/dose strata are comparable, which remain direction-only, and why.
