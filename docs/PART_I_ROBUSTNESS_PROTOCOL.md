# Part I robustness contract

## Purpose

Part I is a qualitative regime-map model, not a calibrated fitness estimator for
a particular species. Before empirical effect sizes are used to constrain any
parameter range, the model must show which conclusions are **structural** and
which depend on a particular functional form.

The present baseline score is

\[
W(A,D,R)=
P(b_0+b_AA)e^{-c_DD}(1-c_RR)
+(1-P)a_RR
-H(f_0+d_AA)(1-e_FD)
-\mathrm{cost}(A,D,R).
\]

The baseline local cross-partial is

\[
\frac{\partial^2 W}{\partial A\,\partial D}
=H d_Ae_F
-Pb_Ac_De^{-c_DD}(1-c_RR)
-c_{AD}.
\]

A positive value is called **local complementarity**, a negative value **local
substitutability**, and a value near zero **locally neutral**. These labels are
about the declared score surface; they do not assert an observed population
trait correlation or an evolutionary endpoint.

## Robustness question

For each declared regime and phenotype neighbourhood, ask:

```text
Does the complementarity / substitutability sign survive
reasonable changes to the response functions and uncertain parameters?
```

The answer is reported as one of:

```text
structurally_robust
conditional_majority
mixed_or_sensitive
```

No result is labelled robust merely because it occurs in the baseline model.

## Functional-form families

Every simulation sweep must include the baseline and the following alternatives.
They retain the same biological meanings while changing curvature.

### 1. Pollination benefit from attraction

```text
baseline:      b_A A
saturating:    b_A A / (1 + q_A A)
```

`q_A=0` recovers the baseline. Positive `q_A` represents diminishing returns of
larger display/reward/visibility to pollination.

### 2. Defence reduction of floral antagonism

```text
baseline:      e_F D
saturating:    e_F D / (h_D + D)
```

The baseline uses a constant marginal defence effect. The alternative allows
large early gains and diminishing protection at high defence.

### 3. Shared attraction–defence allocation cost

```text
baseline:      c_AD A D
curved:        c_AD A D [1 + k_AD(A + D)]
```

`k_AD=0` recovers the baseline. Positive `k_AD` represents escalating joint
investment cost. It is deliberately not inferred from interaction outcomes;
empirical evidence is needed only for a D3 parameterization.

## Required parameter dimensions

The sweep must vary at minimum:

```text
P     pollinator service
H     floral-antagonist pressure
R     reproductive-assurance investment
A,D   local phenotype coordinates
b_A   attraction → pollination strength
d_A   attraction → antagonism tracking
e_F   defence → antagonist reduction
c_D   defence → pollination obstruction
c_AD  shared attraction–defence cost
q_A   attraction saturation
h_D   defence half-saturation
k_AD  curvature of shared cost
```

Leaf-consumer pressure is retained in the complete score but does not enter the
floral A×D mixed partial. It must therefore not be presented as direct evidence
for the floral complementarity condition without an explicit cross-organ model.

## Numerical procedure

For every parameter-regime case, evaluate the analytic cross-partial for each
functional-form family. Report one row per case and one summary row per
regime/phenotype neighbourhood.

```text
sign agreement = number of non-neutral variants with modal sign / number of non-neutral variants

structurally_robust  sign agreement = 1.00 and no neutral/discordant variant
conditional_majority sign agreement >= 0.80
mixed_or_sensitive   otherwise
```

The tolerance for a neutral cross-partial must be predeclared and recorded in
output metadata.

## Empirical bridge

The four-path evidence registry informs only these channel parameters:

```text
A → pollination        b_A
A → antagonism         d_A
B → antagonism         e_F
B → pollination        c_D
```

Empirical effects must not be inserted as raw unstandardized coefficients into
the score. The bridge proceeds in stages:

```text
study × trait × outcome effect sizes
→ outcome/scale-specific meta-analysis
→ standardized parameter envelopes with uncertainty
→ robustness sweep conditioned on those envelopes
```

`c_AD` remains a scenario parameter until independent allocation/cost evidence
exists. It is not estimated from an association between A and B.

## Primary deliverables

```text
part_i_robustness_cases.csv
  one row per functional-form / parameter / regime case

part_i_robustness_summary.csv
  modal sign, agreement, and robustness classification by regime

four_path_effect_registry.csv
  study × trait × outcome records with effect scale, uncertainty, denominator,
  linkage, and causal status
```

## Interpretation boundary

A robust region means only:

> under the stated class of score functions and parameter ranges, the local
> A×D effect has a stable sign.

It does not establish that the same region occurs in all taxa, that its
parameters are universal, or that a measured trait covariance is adaptive.