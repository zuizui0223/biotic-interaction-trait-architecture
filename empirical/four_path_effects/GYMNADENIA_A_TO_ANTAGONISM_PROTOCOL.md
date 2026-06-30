# Predeclared *Gymnadenia odoratissima* A→floral-antagonism analysis

## Scope

This protocol defines exactly one observational effect for the four-path
registry:

```text
A_flower total scent amount → number of eaten flowers / total flowers
```

Source article: Gross, Sun & Schiestl (2016), DOI `10.1371/journal.pone.0147975`.
Public data package: Dryad DOI `10.5061/dryad.dj40r`.

The article publicly declares the Dryad DOI, and the package title begins `Data
from:` followed by the article title. DataCite labels the article relation
`IsCitedBy`; this is recorded as a provenance caveat, not silently upgraded to a
relation-only supplement claim.

## Why this is an A-path

`TotalScentAmount_ngPerL` is measured from floral headspace on the individual
inflorescence and is treated as an **attraction-signal candidate** before fitting
the model. The article describes floral scent as a floral signal important for
pollinator attraction. This role assignment does not assert that total scent is
incapable of affecting antagonists directly; it defines the functional module
used for this synthesis.

## Unit, timing, and outcome

```text
unit:                 individual marked plant / inflorescence
trait timing:         measured at full flower
antagonist outcome:   number of eaten flowers per inflorescence
exposure:             total number of flowers on that inflorescence
outcome timing:       quantified on the day floral signals were measured
linkage key:          PlantID + Year + Region + Population
```

The no-row linkage audit establishes 1,162 unique trait–herbivory links, with
positive numeric flower denominators and no records where eaten flowers exceed
flower count. The article methods establish same-day measurement. The audit
itself retains no observation rows.

## Inclusion set

Include only linked individual records satisfying all of:

```text
1. finite nonnegative TotalScentAmount_ngPerL;
2. finite integer-like NrFlowers > 0;
3. finite integer-like 0 <= NrFlowersEaten <= NrFlowers;
4. nonempty PlantID, Year, Region, and Population; and
5. a complete observed Population × Year stratum.
```

No imputation, winsorisation, manual exclusion, or post-hoc subgroup selection is
permitted.

## Predeclared model

Let \(E_i\) be eaten flowers and \(N_i\) total flowers for individual \(i\). Fit a
binomial-logit model:

\[
E_i \sim \operatorname{Binomial}(N_i, p_i),
\]

\[
\operatorname{logit}(p_i)
= \alpha_{\mathrm{population}\times\mathrm{year}(i)}
+ \beta\,z\{\log(1 + \mathrm{TotalScentAmount}_i)\}.
\]

`z{}` denotes standardization within the complete linked analysis sample. The
population × year intercepts control for baseline spatial and annual differences.

The reported registry effect is:

```text
effect role:        A_to_antagonism
effect measure:     log_odds_ratio
effect estimate:    beta per 1 SD log1p total floral scent
effect uncertainty: conservative quasi-binomial SE
```

The quasi-binomial SE multiplies the model-based covariance by
`max(1, Pearson dispersion)` to avoid underestimating uncertainty. A two-sided
normal approximation produces the 95% CI and p-value.

## Interpretation boundary

This is a conditional **observational association**. Because floral scent and
herbivory were measured on the same day, the model does not demonstrate a
unidirectional causal effect of scent on herbivory, floral defence, or adaptive
selection. It cannot inform individual `A_to_pollination`, either B-path, the
shared A×B cost, or D1/D2/D3 status.

## Output discipline

The extraction script may read the public archive in memory but writes only:

```text
analysis inclusion counts
stratum counts
coefficient, SE, CI, p-value, dispersion
registry-ready effect fields
```

It must not write individual observations, identifiers, raw trait values, or
raw outcome values to repository files or workflow artifacts.
