# Audit of the legacy Megachile R analysis

## Decision

Do **not** refactor `ハキリバチ.R` directly into `01--03` yet.

The script is a valuable exploratory prototype, but it currently combines four different estimands:

\[
\text{geographic co-suitability}
\neq
\text{local resource availability}
\neq
\text{realised leaf cutting}
\neq
\text{trait preference or defence avoidance}.
\]

The formal first chapter must choose one estimand. The defensible first target is:

> **How do the geographically co-suitable plant trait pools of Japanese *Megachile* species differ, conditional on a declared plant universe and a declared spatial model?**

This is not a host-preference or plant-defence claim.

## What remains useful from the prototype

| Legacy block | Decision | Why |
|---|---|---|
| GBIF retrieval functions | rebuild | The general acquisition idea is useful, but the records require a documented QC protocol and versioned downloads. |
| Species-specific bee and plant distributions | retain conceptually | Species-specific spatial surfaces are a reasonable descriptive input, provided their estimation and scale are audited. |
| Trait-table construction | rebuild | Trait provenance, units, measurement context, and missingness need explicit handling. |
| Overlap-weighted trait centroid | retain after correction | This can describe a geographic co-suitability-weighted trait centroid, but not use or preference. |
| PCA visualisation | retain as descriptive only | Axis labels must come from reported loadings, not assumed biological meanings. |
| Hypervolume | postpone | The current construction produces artificial replicated points and is not a reliable primary result. |
| Schoener D final block | remove from current script | `bee_use_matrix` is not constructed in the script, so this block has no defined input. |

## Code-level findings

### A. Occurrence acquisition and record identity

The plant function requests GBIF records by scientific name, country, and coordinates, then removes only missing or zero coordinates and exact duplicate coordinates. It does not retain record identifiers or metadata needed for later filtering, such as basis of record, uncertainty, year, taxonomic match, institution, or occurrence status. The same minimal filtering is used for bees.

**Consequence:** the analysis cannot yet diagnose coordinate error, cultivated records, fossil/observation heterogeneity, repeated institutional sampling, temporal mismatch, or taxonomic ambiguity.

**Required replacement:** save raw query output outside version control, record query date and GBIF download/DOI where possible, then produce a QC table with one row per retained record and explicit exclusion reasons.

### B. Plant-list construction is undefined

The analysis begins from a hard-coded list of 12 plant species. The script does not state whether these are documented leaf-cutting hosts, field observations, plants with available TRY traits, or an illustrative list.

**Consequence:** every trait centroid is conditional on an unexplained and very narrow plant universe. It cannot be interpreted as a Japanese resource pool or a potential host pool.

**Required replacement:** define one of the following before modelling:

1. a documented Japanese *Megachile* host universe;
2. a regional vascular-plant universe filtered by habitat and phenology;
3. a host-plus-background design for an eventual realised-use model.

The first formal analysis may use a **documented candidate plant universe**, but must report inclusion criteria and trait coverage.

### C. Species relabelling bug after failed plant queries

After null plant-query results are removed, the script assigns species labels using the original index:

```r
gbif_leaf_list12 <- gbif_leaf_list12[!sapply(gbif_leaf_list12, is.null)]
for(i in seq_along(gbif_leaf_list12)){
  gbif_leaf_list12[[i]]$species <- leaf_final12[i]
}
```

If any query failed before the end of the original vector, later successful results can receive the wrong species name.

**Decision:** rebuild. Store the species name together with each query result before filtering null results; never restore names by positional index.

### D. Bee species list may be incomplete and sampling-dependent

The script derives Japanese *Megachile* species from one limited generic-occurrence query, then uses the returned species keys for subsequent searches. It also keeps species with at least 20 unique coordinate pairs.

**Consequence:** the candidate bee set depends on the initial GBIF retrieval and raw sampling density. A 20-record threshold is not a distribution-model validation criterion and does not address spatial clustering.

**Required replacement:** obtain a taxonomically curated Japan checklist or document a GBIF-derived candidate list with pagination/completeness checks; separately define occurrence thresholds, spatial thinning, and minimum independent spatial blocks for each modelling method.

### E. Environmental model is not declared

Both plant and bee models use `Env_r`, but the script does not construct it. The script therefore does not report raster sources, time period, resolution, collinearity filtering, geographic mask, accessible area, or whether plants and bees are modelled over the same calibration region.

**Decision:** no SDM result can be treated as reproducible until `Env_r` is replaced by a declared environment object and metadata file.

### F. The SDM protocol is underspecified

`stack_modelling()` is called with GLM and random forest, one repetition, and no visible specification of background/pseudo-absence design, model evaluation, spatial cross-validation, tuning, thresholding, extrapolation policy, or algorithm weights.

**Consequence:** the projection surfaces are exploratory outputs only. They cannot support formal comparative overlap claims yet.

**Required replacement:** choose either a deliberately descriptive spatial smoothing approach or a fully specified SDM protocol. For a formal SDM path, each species needs:

- calibration extent / accessible area;
- bias treatment or target-group background;
- spatial thinning;
- spatially blocked evaluation;
- predictor selection and correlation policy;
- algorithm tuning and ensemble rule;
- transfer/extrapolation diagnostics.

### G. Product of species projections is not interaction probability

For bee \(b\) and plant \(i\), the script computes:

\[
O_{bi}=\sum_x S_b(x)S_i(x),
\]

where the projected raster values are multiplied and summed.

This quantity may be retained as a **spatial co-suitability index** only after raster alignment and scale checks. It is not automatically:

- local plant biomass;
- leaf availability;
- probability of encounter;
- realised leaf cutting;
- host preference.

**Required replacement:** name the quantity `co_suitability_index` or another explicitly descriptive term. Add normalised alternatives as sensitivity analyses, such as binary threshold overlap, proportional overlap after each surface is normalised to sum to one, and geographic co-occurrence based on buffered occurrences without SDMs.

### H. Raster alignment and scale are not validated

Plant rasters are resampled onto each bee raster inside the overlap loop. No shared template, extent check, mask, CRS check, cell-area correction, or resampling method is declared.

**Consequence:** overlap can change with the chosen bee raster grid and resampling behaviour. Summing cell values also gives different emphasis if cell areas vary geographically.

**Required replacement:** create one fixed equal-area template and mask before any overlap calculation; explicitly specify interpolation method; use cell-area weights where needed; fail loudly if CRS, extent, resolution, or NA masks differ unexpectedly.

### I. Trait aggregation is biologically and statistically heterogeneous

The script maps broad TRY names to six labels and averages `StdValue` by species and trait. It does not demonstrate that all values are in comparable units, that transformations are appropriate, or that observations are comparable across organs, developmental states, environments, and measurement protocols.

**Consequence:** a mean may merge incompatible measurements. The resulting PCA and centroids may reflect database composition rather than species traits.

**Required replacement:** build a trait dictionary with accepted TRY trait IDs/names, units, permitted value ranges, transformation, organ/context filters, and source counts. Preserve within-species uncertainty rather than reducing every species immediately to one mean.

### J. Missing traits bias the weighted centroids

The current centroid is calculated as:

```r
sum(leaf_traits_sub[, tr] * w, na.rm = TRUE)
```

When a species has a missing value, its weight is discarded from the numerator but the remaining weights are not renormalised for that trait.

**Consequence:** trait centroids can be biased downward or upward solely because trait coverage differs among plants.

**Required replacement:** for each trait \(t\), calculate

\[
\mu_{bt}=\frac{\sum_{i\in\mathcal O_t} w_{bi}x_{it}}
{\sum_{i\in\mathcal O_t} w_{bi}},
\]

and report the retained weight mass \(\sum_{i\in\mathcal O_t}w_{bi}\). Analyses with low retained mass should be flagged, not silently imputed.

### K. PCA is currently fragile

The first PCA uses `na.omit(trait_mat_clean)`, potentially leaving a tiny and non-representative subset of 12 plants. Later PCA uses mean-imputed traits. These are different data-generating assumptions, but their results are not compared.

The final graph labels PC1 and PC2 as named leaf gradients without showing variable loadings.

**Decision:** retain PCA only as a descriptive visualisation after trait QC. Report sample size, trait coverage, loadings, explained variance, and sensitivity to complete-case versus uncertainty-aware imputation. Do not name axes without loading evidence.

### L. Hypervolume construction is not valid as a primary ecological niche estimate

The script replaces missing traits by global means, duplicates each plant species' single mean trait vector according to rounded overlap weights, and fits a Gaussian hypervolume to those duplicated points.

**Consequence:** the estimated volume is driven by arbitrary `n_sample`, rounding, duplicate observations, mean imputation, and bandwidth estimation on pseudo-replicates. It contains no within-species trait variation and should not be called a utilisation hypervolume.

**Decision:** remove from the initial formal analysis. Reconsider only after a justified weighted-distribution method and a plant universe with enough independent trait observations are available.

### M. The final Schoener-D section is disconnected

The script normalises `bee_use_matrix`, but never creates it.

**Decision:** remove until a real interaction table exists. Schoener D may later compare observed or modelled plant-use compositions, but not be run on an undefined object.

## Formal analysis specification after audit

### First estimand

For each bee species \(b\), estimate a **geographic co-suitability-weighted plant trait summary** over a declared candidate plant set \(\mathcal P\):

\[
\mu_{bt}=\frac{\sum_{i\in\mathcal P}w_{bi}x_{it}}
{\sum_{i\in\mathcal P}w_{bi}},
\]

where \(w_{bi}\) is a declared and sensitivity-tested spatial co-suitability weight. This is a descriptive macroecological quantity.

### Minimum outputs

1. candidate bee and plant lists with taxonomy and inclusion rationale;
2. occurrence-QC table and retained-record map;
3. trait-coverage table and unit/context dictionary;
4. co-suitability matrix under at least three spatial constructions;
5. trait centroids with coverage-weight diagnostics;
6. null comparison preserving geography or regional plant-pool composition;
7. sensitivity table across occurrence QC, spatial construction, plant universe, and trait missing-data policy.

### Claims permitted at this stage

- Bee species differ, or do not differ, in the *modelled geographic co-suitability-weighted trait pools*.
- Any difference is stable or unstable to named sensitivity settings.

### Claims not permitted at this stage

- A bee prefers a trait.
- A bee avoids plant defence.
- A trait prevents cutting.
- A plant is a host without an interaction record.
- Co-suitability explains a realised interaction network.

## Gating criteria before building `01--03`

All conditions below must be met:

```text
[ ] bee taxon list and plant universe have explicit inclusion rules
[ ] occurrence records carry QC provenance and spatial thinning decisions
[ ] environment/grid/background rules are declared
[ ] co-suitability has a restricted descriptive interpretation
[ ] trait dictionary, units, and missing-data plan are defined
[ ] weighted centroids renormalise within trait
[ ] at least one geography-preserving null is implemented
[ ] hypervolume is excluded from primary inference
[ ] no undefined objects or machine-specific file paths remain
```

Only then should the old script be split into a reproducible formal workflow.
