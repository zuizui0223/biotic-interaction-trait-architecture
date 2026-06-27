# First regime-map model

## Purpose

This module is a qualitative simulation scaffold. It asks which investment vector

\[
(A,D,R)
\]

maximises a declared score under a specified interaction regime

\[
(P,H,L).
\]

It is not a parameterised estimate of fitness for Campanula, Cirsium, Megachile host plants, or any other natural system.

## Score

\[
W=
B_{\rm outcross}
+B_{\rm assurance}
-L_{\rm floral\ damage}
-L_{\rm leaf\ damage}
-C.
\]

The implemented channels are:

\[
B_{\rm outcross}=P(b_0+b_AA)e^{-c_DD}(1-c_RR),
\]

\[
B_{\rm assurance}=(1-P)b_RR,
\]

\[
L_{\rm floral\ damage}=H(d_0+d_AA)(1-e_FD),
\]

\[
L_{\rm leaf\ damage}=L\ell_0(1-e_LD),
\]

with quadratic investment costs and an optional shared attraction-defence cost.

## Interpretation

- `defence_pollinator_cost` controls whether defence reduces pollinator access.
- `attraction_tracking` controls whether floral antagonists track attractive displays.
- defence efficacies control how selectively D reduces floral or leaf damage.
- assurance becomes valuable when pollinator service is low, but can dilute outcross return.

Therefore an apparent attraction-defence trade-off is a model outcome conditional on these mechanisms, not an assumption.

## Output

The optimiser uses a finite \([0,1]^3\) grid and returns the highest-scoring phenotype. It assigns only coarse labels:

```text
open_attraction
attraction_withdrawal
dual_insurance
guarded_attraction
defence_first
mixed
```

Grid optima can tie. The output is a sensitivity object: repeat the sweep over parameter combinations and inspect where labels are stable, not merely the default map.

## Next implementation step

Add a parameter-sweep layer that records trait-covariance signs and strategy frequencies across model assumptions. Only after that should the model be compared with Megachile, Campanula, or Cirsium data.
