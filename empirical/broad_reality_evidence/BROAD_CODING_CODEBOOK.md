# Broad evidence coding codebook v1

## Candidate-level source screening

Each priority candidate receives exactly one source-screening decision.

| Field | Allowed values | Rule |
|---|---|---|
| `source_screen_status` | `unassessed`, `included_for_source_coding`, `excluded` | Include only primary empirical studies with a usable source. |
| `source_access_status` | `abstract_only`, `fulltext_available`, `data_available`, `fulltext_and_data_available`, `inaccessible` | Describe access, not scientific quality. |
| `study_type` | `observational`, `manipulation`, `comparative`, `review`, `nonbiological`, `other` | Use methods, not title wording. |
| `study_cluster_id` | reproducible shared-panel label | Same field panel/data set = same cluster, even across papers. |

An excluded candidate remains in the retrieval receipt; exclusion is never
implemented by deletion.

## Route records

Create one row for every **direct** pathway actually assessed by a study.

```text
A_to_pollination
A_to_antagonism
B_to_antagonism
B_to_pollination
```

A joint-channel study can yield several route records, but only when each route
has a distinct stated trait–outcome comparison. Do not create a route record
from a discussion-only connection.

### Trait-role rules

```text
A = flower colour, visual contrast, guide, size, display, orientation, scent,
    reward, nectar quantity, or another predeclared attraction/access trait.

B = flower-specific chemical deterrent, physical barrier, access resistance, or
    floral trait independently justified as reducing antagonist access/damage.
```

The following are not B by default:

```text
leaf defence
vegetative herbivory
post-damage floral response without a measured pre-existing floral barrier
flower number alone
floral scent unless its barrier role is explicitly justified
```

### Outcome classes

| Outcome class | Channel | Examples |
|---|---|---|
| `visitation_rate` | P | visits per flower/time, visitor probability |
| `pollinator_preference_or_foraging` | P | choice proportion, feeding frequency/duration, treatment preference in a controlled assay |
| `pollen_transfer` | P | pollen deposition/removal, stigma pollen load |
| `pollination_success` | P | declared pollination treatment outcome, compatible pollen limitation proxy |
| `floral_damage_proportion` | H | flowers/ovules damaged divided by exposure total |
| `florivore_abundance` | H | florivore count or probability per declared exposure |
| `robbery_rate` | H | nectar/pollen robbery with stated denominator |
| `predation_probability` | H | flower or pre-dispersal seed predation event probability |
| `fruit_set`, `seed_set` | W, not P by default | reproductive fitness outcomes |

`pollinator_preference_or_foraging` is a P-channel response, but is not silently
pooled with `visitation_rate`: a controlled feeder/choice assay has a different
unit and exposure definition than visits to intact flowers in the field.

Fruit set and seed set may be coded as pollination only when the paper directly
establishes them as the declared pollination outcome and antagonism is not a
plausible unmodelled route. Otherwise they remain fitness context and are not
pooled with visitation or pollen transfer.

## Direction coding

Orient all direct route records as:

> more declared trait/barrier → more declared outcome

Then code the paper's stated or recoverable result as:

```text
positive      positive association/effect in that orientation
negative      negative association/effect in that orientation
mixed         contradictory results across predeclared comparable analyses
null          explicit null/no detectable association
not_reported  trait and outcome both occur but no direction is recoverable
```

Do not infer a sign from a figure without readable scale, a p-value without a
coefficient/direction, or a narrative claim unsupported by a result.

## Primary-record selection

For a `study_cluster × route × trait_class × outcome_class × design_class` cell,
select one primary sign record and, if quantitatively eligible, one primary
effect. Prefer in this order:

```text
1. prespecified main model over sensitivity model
2. model with stated confounder adjustment over unadjusted duplicate
3. shared-unit measurement over aggregate association
4. longer/declared observation exposure over partial duplicate
5. public table/data recoverable estimate over prose-only sign
```

Keep non-primary results in notes; do not count them as separate clusters.

## Quantitative extraction

Allowed transformations are:

```text
reported_effect   reported compatible estimate and SE
log_response_ratio group means, SDs, and n
log_odds_ratio     2×2 event/non-event counts
fisher_z           Pearson r and n
hedges_g           group means, SDs, and n
```

`standardized_beta` is only used as reported with a reported/recoverable SE. It
is never pooled with response ratios, odds ratios, correlations, or standardized
mean differences.

## Source traceability

Every included route record and effect needs:

```text
DOI or candidate ID
source basis
source locator (table, figure, model, supplement, or data file)
coder ID and date
context note describing trait/outcome orientation
```

The broad direction map describes the coded corpus. It is not a causal
meta-analysis and cannot substitute for a direct D1/D2 design.