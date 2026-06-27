# Megachile leaf-resource chapter

## Purpose

This chapter asks whether Japanese leaf-cutter bee species occupy different **geographically accessible leaf-trait landscapes**, and later whether realised leaf-cutting use differs from availability after accounting for plant traits.

## Existing source

The repository's legacy `ハキリバチ.R` script is retained unchanged as the historical prototype. It currently:

- downloads Japanese GBIF occurrences for a selected plant list and *Megachile*;
- estimates stacked SDMs;
- weights plant leaf traits by geographic overlap with bee distributions;
- calculates bee-specific trait centroids and trait hypervolumes.

That prototype is the availability layer only.

## Reproducible workflow to build next

```text
01_taxonomy_and_occurrence_qc.R
02_accessible_trait_landscape.R
03_sdm_and_overlap_sensitivity.R
04_host_record_harmonisation.R
05_realised_use_given_availability.R
06_trait_niche_and_null_models.R
07_figures_and_tables.R
```

## Data contracts

### `plants.csv`

```text
plant_id,accepted_name,trait_source,longitude,latitude
```

### `bees.csv`

```text
bee_id,accepted_name,longitude,latitude,record_source
```

### `leaf_traits.csv`

```text
plant_id,SLA,LDMC,leaf_thickness,leaf_density,leaf_area,trait_coverage
```

### `host_records.csv`

```text
bee_id,plant_id,interaction_type,record_basis,location_id,year,source,citation
```

`interaction_type` must distinguish direct cutting/nesting-material evidence from vague association, floral visitation, or co-occurrence.

## Main estimands

Availability-weighted centroid:

\[
\boldsymbol\mu_b=\frac{\sum_i O_{bi}\mathbf x_i}{\sum_i O_{bi}}.
\]

Conditional realised-use model:

\[
\operatorname{logit}\Pr(U_{bi}=1)=
\beta_0+\beta_1O_{bi}+\boldsymbol\beta_2^\top\mathbf x_i+u_b+v_i.
\]

The first estimand describes accessible resource space. The second is needed before discussing conditional trait selection or avoidance.

## Required safeguards

- Do not infer host preference from distribution overlap alone.
- Do not treat a GBIF occurrence as an interaction record.
- Do not label leaf economic traits as defence without a stated mechanism.
- Report sensitivity to occurrence filters, background extent, SDM method, and missing-trait handling.
