# Broad evidence calibration batch 1: abstract-level adjudication

## Frozen source receipt

```text
Crossref harvest workflow run: 28495603975
artifact:                      8000888585
artifact digest:               sha256:9f89f27c6bd710068c2a9f5106bc20363a8bc33984f46018f9817b9f5351ae93
calibration candidates:        24
Crossref DOI lookups:          24 successful
Crossref deposited abstracts:  24 available
```

This batch is an **abstract-resolution source screen**, not a substitute for
full-text extraction. The source packet is retained in the artifact and is the
basis for every decision below.

## Candidate-level outcome

```text
included_for_source_coding: 19
excluded:                     4
unassessed:                   1
```

The excluded records were not deleted. They remain visible with a reason in
`batch_1_source_screening.csv`.

```text
leaf-only herbivory / no direct floral predictor: 1
purely descriptive trait-visitor biology:         2
review or framework paper:                         1
unusable deposited abstract:                       1 (unassessed, not excluded)
```

## Direct route records at abstract resolution

Eight source-supported direct records were retained in
`batch_1_route_records.csv`:

| Route | Records | What entered |
|---|---:|---|
| `A_to_pollination` | 5 | display, visual signal, or scent with visitation/pollen-transfer outcomes |
| `A_to_antagonism` | 1 | colour morph and floral-damage comparison |
| `B_to_antagonism` | 2 | flower chemical traits and florivore/antagonist response |
| `B_to_pollination` | 0 | no direct barrier-to-pollination comparison at abstract resolution |

This is not an effect-size result. All eight records are `abstract_only`, use
sign coding only, and have no numerical extraction.

## Main calibration decisions

### 1. Search routes are not biological roles

The discovery queue placed several scent, display, or pollination studies in
`B_to_pollination`. The abstracts did not establish a flower-specific barrier
role. These studies were not reclassified as B merely because the search query
matched chemical vocabulary.

### 2. Florivory studies often test a different arrow

Several attractive candidates test:

```text
florivory -> floral signal
florivory -> pollination
florivory -> fitness
nectar robbery -> fitness
```

Those are biologically useful joint-channel studies, but they are not direct
`A_to_pollination`, `A_to_antagonism`, `B_to_antagonism`, or
`B_to_pollination` records unless a pre-existing declared floral trait predicts
the relevant outcome.

### 3. Fitness remains distinct from pollination

Flower scent and seed set in *Polemonium*, and experimental florivory effects on
fruit or seed production, remain W-context records. They do not become P records
without a direct declared pollination outcome or an identified pollination path.

### 4. Abstracts can show direction but not numerical compatibility

The batch contains source-level directional statements such as:

```text
larger display -> more visitor activity
higher floral chemical defence -> lower florivore response
colour/trait effects that reverse or differ among pollinator contexts
```

None has a recoverable compatible metric plus uncertainty at abstract
resolution. Therefore `batch_1_effect_extractions.csv` is deliberately not
created, and no stratum is pooled.

## Immediate implication for bulk coding

The codebook does not need to be relaxed. The batch confirms why the broad route
needs two layers:

```text
broad direction map
    can retain direct but heterogeneous abstract/full-text evidence

compatible mini-meta-analysis
    remains narrow and waits for metric, uncertainty, orientation, and
    independent-panel evidence
```

The next batch should oversample the absent `B_to_pollination` route and source
studies with experimental flower-specific chemical or physical barriers and
visitor outcomes. It should not simply add more floral-scent studies.