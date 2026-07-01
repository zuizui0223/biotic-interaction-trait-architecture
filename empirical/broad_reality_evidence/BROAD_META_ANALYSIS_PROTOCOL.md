# Broad real-world evidence: meta-analysis design v1

## Position in the research program

```text
Part I   mathematical robustness map is the primary inferential object
Part II  broad literature evidence tests support, contradiction, heterogeneity, and gaps
Part III strict four-path records are high-quality quantitative anchors
```

The broad synthesis does **not** estimate universal biological coefficients for
Part I. It evaluates whether real-world studies are directionally compatible
with the channel assumptions, where that compatibility changes with trait class,
outcome, study design, and context.

## Questions

For each direct channel, ask separately:

```text
A_to_pollination   does greater declared attraction associate with greater pollination?
A_to_antagonism    does greater declared attraction associate with greater floral antagonism?
B_to_antagonism    does greater declared flower barrier associate with less floral antagonism?
B_to_pollination   does greater declared flower barrier associate with less pollination?
```

The model-declared channel expectations are:

| Route | Expected observed association | Part I parameter |
|---|---|---|
| `A_to_pollination` | positive | `b_A` |
| `A_to_antagonism` | positive | `d_A` |
| `B_to_antagonism` | negative | `e_F` |
| `B_to_pollination` | negative | `c_D` |

These are channel assumptions, not universal claims. A contrary sign is a
potential trait-role, context, measurement, or regime boundary; it is not
silently recoded or discarded.

## Unit of evidence

```text
screening unit         candidate work
shallow coding unit    study × direct route × trait class × outcome class
quantitative unit      study-cluster × route × trait class × outcome class × metric × design
```

`study_cluster_id` represents a genuinely independent data-generating panel.
Multiple papers, traits, time points, or models from one panel are not
independent meta-analytic replicates.

## Layer 1: directional evidence map

All source-coded primary studies can contribute one primary direction record per
independent cluster and route/trait/outcome/design cell:

```text
positive
negative
mixed
null
not_reported
```

The map reports cluster-level counts and the fraction of evaluable signs that
match the declared channel expectation. It does not treat sign counts as causal
effect estimation, and it never weights a sign by citation count or metadata
rank.

Direction-map interpretation:

```text
< 3 evaluable independent clusters  -> insufficient_directional_clusters
>= 3 and >= 80% compatible signs    -> mostly_compatible_with_channel_assumption
>= 3 and <= 20% compatible signs    -> mostly_contradictory_to_channel_assumption
otherwise                            -> mixed_or_context_dependent
```

The labels describe the versioned corpus and coded stratum only.

## Layer 2: compatible quantitative mini-meta-analyses

Numerical pooling is allowed only inside a predeclared stratum with the same:

```text
route
trait class
outcome class
effect metric
design class
```

No conversion is made between unrelated ecological outcomes or causal designs.
For example, pollinator visitation is not pooled with fruit set, and an
observational trait association is not pooled with a defence manipulation.

Supported effect metrics are:

| Metric | Positive value means | Typical source form |
|---|---|---|
| `log_response_ratio` | high-trait/treatment group has higher outcome | group means, SDs, n |
| `log_odds_ratio` | high-trait/treatment group has higher event odds | 2×2 counts |
| `fisher_z` | positive trait–outcome correlation | Pearson r, n |
| `hedges_g` | high-trait/treatment group has higher outcome | group means, SDs, n |
| `standardized_beta` | positive standardized trait–outcome association | reported model coefficient + SE |

Every extracted effect is oriented so that a positive value means **more declared
trait or barrier, more declared outcome**. This preserves the model-facing
interpretation: `A→P` and `A→H` are expected positive, while `B→H` and `B→P`
are expected negative.

### Pooling rule

```text
k < 3 independent clusters  -> no pooled estimate; report effects and gap only
k >= 3                       -> exploratory DerSimonian–Laird random-effects estimate
k >= 5                       -> stability-eligible random-effects estimate
```

The output always reports `k`, fixed-effect heterogeneity `Q`, `I²`, and
DerSimonian–Laird `tau²`. A pooled direction is compared with the channel
assumption but is never inserted as a raw Part I parameter.

## Layer 3: bridge to Part I

The broad map may indicate which channel assumptions have consistent,
contradictory, or context-specific real-world support. Only effect strata with:

```text
- a compatible outcome/metric/design definition;
- at least five independent study clusters;
- transparent uncertainty and heterogeneity diagnostics;
- trait-role interpretation preserved;
```

may inform a *standardized scenario envelope* for sensitivity analysis. Strict
four-path records remain the stronger calibration anchors. Shared cost `c_AD`
remains a scenario parameter unless independent allocation/cost evidence is
obtained.

## Coding and extraction contracts

```text
broad_source_screening_matrix.csv
    one row per priority candidate; source access and inclusion decisions

broad_route_records.csv
    one row per source-coded study × direct route × trait × outcome record

broad_effect_extractions.csv
    one row per candidate quantitative effect; raw data or reported effect with
    orientation, uncertainty, study cluster, and eligibility state

broad_meta_analysis_strata.csv
    predeclared exact compatibility strata and thresholds
```

A source record can contribute to the direction map even when it has no usable
numerical effect. A numerical effect cannot enter a pool unless it passes its
metric, orientation, uncertainty, and independence checks.

## Explicit prohibitions

```text
- Do not pool signs as effect sizes.
- Do not pool different trait classes merely because both are called "attraction" or "defence".
- Do not pool visitation, pollen transfer, fruit set, and seed set.
- Do not treat multiple outcomes from a shared panel as independent without a declared multivariate model.
- Do not invert a contrary effect to force agreement with the model.
- Do not call a broad meta-analysis a direct D1/D2 test.
```

## Primary outputs

```text
broad_direction_map.csv
broad_meta_analysis_summary.csv
broad_meta_analysis_effects_used.csv
broad_meta_analysis_diagnostics.json
```

The key empirical result is a structured map of support, contradiction,
heterogeneity, and missingness across the four channels—not a single global
mean effect.