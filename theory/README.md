# Theory and simulation specification

## Objective

Map mutualist and antagonist regimes to qualitative floral attraction--defence
trait architectures without pretending that the first model is an empirically
calibrated evolutionary prediction.

## Active empirical interpretation

```text
A = A_flower: floral display, nectar guide, flower size, nectar reward, orientation
D = B_flower: flower-specific defence or pollinator-access restriction
```

Examples of `D` include floral chemical deterrents, trichomes, spines, sticky
structures, and other barriers that are measured on the attacked or visited
flowering organ. Leaf toughness, LDMC, leaf chemistry, and stem resistance are
not automatically observations of `D` in the active A--D result.

The current score retains reproductive assurance `R` as a theoretical sensitivity
term. It is varied in sensitivity analyses, but no active L1/L2 empirical module
calibrates it.

## Interaction regimes

```text
P: pollinator service
H: floral herbivore / florivore pressure
L: leaf consumer pressure
```

The simulator sweeps a low-dimensional parameter grid and classifies strategies
rather than simulating whole plant genomes.

## Exact local A--D condition

For the implemented score, the mixed partial

\[
\frac{\partial^2 W}{\partial A\,\partial D}
=
H d_A e_F
- P b_A c_D e^{-c_DD}(1-c_RR)
- c_{AD}
\]

separates local complementarity from local substitution. It is exact for the
current score, but it is not an empirical covariance prediction by itself. The
implementation and required bridge to global data are documented in
`docs/theory_to_network_prediction_contract.md`.

The broad literature interface does not alter the expression. It maps which terms
have abstract-level coverage and limited source-coded sign/context support; see
`docs/broad_evidence_to_regime_interface.md`.

## Strategy classes to detect

```text
open attraction:       A high, D low
guarded attraction:    A high, D high
defence-first:         A low,  D high
mixed:                 no coarse corner label
```

## Falsifiable model-family predictions

1. Attraction and defence are locally substitutable when defence directly
   reduces pollinator access or shares a binding allocation budget with
   attraction.
2. Attraction and defence are locally complementary when floral antagonists
   track attractive displays and defence selectively reduces their damage.
3. A positive or negative covariance among simulated optima is a separate,
   grid-dependent result; stability must be assessed over declared parameter
   scenarios.
4. Leaf-consumer pressure affects defence directly, but it changes the floral
   A--D relation only through a separately declared shared cost, architecture,
   or distribution of regimes.

## Link to broad literature analysis

The broad L1/L2 layer does **not** estimate model coefficients. It reports:

```text
A -> P candidate coverage      maps to the sign/context status of b_A
A -> H candidate coverage      maps to the sign/context status of d_A
B -> H candidate coverage      maps to the sign/context status of e_F
B -> P candidate coverage      maps to the sign/context status of c_D
```

`c_AD` requires matched attraction/defence allocation evidence, and `c_R*R`
requires a reproductive-assurance observation model. Both remain sensitivity
axes. A direct A--D test remains deferred until a matched dual-layer dataset
provides comparable plants, sites, and times.
