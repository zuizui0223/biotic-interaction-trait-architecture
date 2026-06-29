# Theory and simulation specification

## Objective

Map mutualist and antagonist regimes to qualitative attraction--defence trait
architectures without pretending that the first model is an empirically
calibrated evolutionary prediction.

## Minimal modules

```text
attraction A
  floral display, nectar guide, flower size, nectar, orientation

defence/access D
  leaf toughness, LDMC, thickness, spines, sticky secretion,
  chemical deterrence, physical access barriers
```

The current score also retains reproductive assurance `R` as a sensitivity term
because assurance can dilute attraction-mediated outcross return. It is varied
in theoretical sensitivity analyses, but no separate global-data `R` module is
part of the active backbone. Plant-material-use modules remain possible future
extensions.

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
implementation and the required bridge to global data are documented in
`docs/theory_to_network_prediction_contract.md`.

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
4. Leaf-consumer pressure affects defence directly, but it changes the A--D
   relation only through shared costs, shared architecture, or the distribution
   of regimes in the current model.

## Link to global analysis

The global-network layer tests observational signatures, not the score directly:

```text
A <-> pollination-network structure
D <-> organ-matched antagonist-network structure
```

A direct A--D test is deferred until a matched dual-layer dataset provides both
interaction contexts for comparable plants, sites, and times.
