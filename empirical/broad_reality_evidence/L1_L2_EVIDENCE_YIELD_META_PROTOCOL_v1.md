# L1/L2 broad evidence synthesis v1

## Decision

The primary analysis uses the fixed L1/L2 corpus broadly and shallowly. It does
not treat the five-study numeric queue as the gatekeeper for the project, and it
does not pretend that a query hit is a biological effect.

The design has three non-interchangeable parts:

```text
1. broad abstract evidence map       where the literature attends to A, B, P, H
2. audit-yield calibration           how often shallow candidates are direct-route studies
3. source-direction anchors          which model branches have limited sign/context support
```

The first part is the main empirical overview. The second is a calibration and
sensitivity analysis. The third is the narrow connection to the fixed regime
model.

## Inputs

- **L1:** all deduplicated Crossref candidates in the fixed corpus.
- **L2:** priority and biological-context memberships retained as screen strata,
  not as the only analysis population.
- **Fixed abstract packet:** Crossref abstract lookups only for candidate IDs
  already present in L1 and already marked abstract-available by the original
  harvest. No new discovery query is issued.
- **Frozen audit:** route x screen-group source-screen outcomes.
- **Direction registry:** source-adjudicated, low-count route/direction anchors.

## Primary broad abstract map

Each accessible abstract receives transparent high-recall labels for:

```text
floral organ context
A: attraction/display/signal candidate language
B: defence/access-barrier candidate language
P: pollination/visitor/pollen outcome language
H: florivory/damage/robbery outcome language
W: reproductive output language
review versus empirical-language signal
shared-cost/allocation language
```

The resulting A--P, A--H, B--H, B--P, and joint-channel counts are **abstract
co-mention candidate coverage**. They map the architecture of the evidence base;
they do not establish a measured causal route, sign, or effect magnitude.

## Audit-yield calibration

For route `r` and L2 screen group `g`:

```text
Y_rg ~ Binomial(n_rg, theta_rg)
theta_rg ~ group-level Beta(alpha_g, beta_g)
```

This is a secondary methodological analysis. It estimates how the frozen audit's
direct-route yield varies across the existing screen strata. Equal-yield
projections are sensitivity summaries, never confirmed study counts.

A route-wise priority versus biological-nonpriority log odds ratio can be pooled
as a random-effects **screen-enrichment** analysis. It is not a flower-trait
effect meta-analysis.

## Connection to the unchanged regime model

The exact local condition is not re-fit or altered:

```text
∂²W/∂A∂D = H*d_A*e_F - P*b_A*c_D*exp(-c_D*D)*(1-c_R*R) - c_AD
```

The broad map supplies literature coverage for the four observable channels:

```text
A -> P  informs sign/context of b_A
A -> H  informs sign/context of d_A
B -> H  informs sign/context of e_F
B -> P  informs sign/context of c_D
```

`c_AD` requires matched attraction--defence allocation evidence and `c_R*R`
requires reproductive-assurance data. Both remain declared sensitivity axes under
the active L1/L2 program.

The model interface classifies each term as directionally anchored,
condition-dependent, or not identified. It never turns publication counts or
abstract hits into numerical parameter values.

## Boundaries

- Query memberships are overlapping discovery strata, not independent biological
  studies.
- Crossref abstracts are shallow source metadata; they are not effect sizes.
- An observed zero in a sparse audit cell is not a biological null.
- Separate A/P and B/H literatures cannot establish observed A--B covariance or a
  shared cost without matched units.
