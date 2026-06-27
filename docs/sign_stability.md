# Parameter-sweep sign stability

## Why this layer is necessary

The first regime map gives one optimal trait architecture for one parameter vector. That is only a conditional example. This layer tests whether the sign of the attraction--defence association across regime optima persists after changing declared model assumptions.

## Estimand

For one parameter scenario \(s\), let \((A_j,D_j,R_j)\) be the finite-grid optimum for regime-grid point \(j\). The reported association is

\[
\operatorname{Cov}_s(A,D)=\frac{1}{J}\sum_{j=1}^{J}(A_j-\bar A)(D_j-\bar D).
\]

It is **not** an individual-level phenotypic covariance, a genetic covariance, or an estimate from data. It is a summary of how optimal investments co-occur across the explicitly selected interaction regimes.

## Interpretation categories

For every parameter scenario the model reports:

```text
positive
negative
zero
undefined
```

Across scenarios it reports:

```text
stably_positive
stably_negative
stably_zero
mixed
insufficient
```

`mixed` is an informative outcome: it means the current model class predicts a sign reversal under different, biologically interpretable assumptions. It is not a failure to obtain a result.

## Canonical mechanism contrasts

The initial scenario set contains:

- **costly defence**: defence blocks pollination and weakly reduces damage;
- **guarded attraction**: attractive displays attract antagonists, but defence selectively prevents damage while barely blocking pollination;
- **weak tracking**: attractive display does not meaningfully increase antagonism, while defence has access cost;
- **efficient assurance**: reproductive assurance is cheap and valuable under pollinator limitation.

The expected result is not one universal sign. In particular, costly defence should favour negative A--D association, while guarded attraction can favour positive A--D association.

## Empirical use

Megachile, Campanula, and Cirsium observations may eventually be coded as regime descriptors and trait-module values. They cannot be used to validate a scenario merely because the observed sign agrees with it. A valid comparison requires an explicit observation model, sampling/phylogenetic structure, and a competing-mechanism check.
