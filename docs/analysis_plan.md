# Analysis plan

## 1. Theory layer

### State variables

\[
\mathbf z=(A,D,R),\qquad \mathcal I=(P,H,L),
\]

where \(P\) is pollinator service, \(H\) is herbivore/florivore pressure, and \(L\) is leaf-cutter or leaf-consumer pressure.

### Minimal fitness decomposition

\[
W(\mathbf z;\mathcal I)=
B_{\rm outcross}(A,D;P)
+B_{\rm assurance}(R;P)
-L_{\rm floral\ damage}(A,D;H)
-L_{\rm leaf\ removal}(D;L)
-C(A,D,R).
\]

The first simulations will not claim a calibrated natural fitness surface. Their role is to identify qualitative regime boundaries where the sign of association between trait modules changes.

### First theory questions

1. When is \(\operatorname{Cov}(A,D)<0\) expected from direct allocation or access costs?
2. When does antagonist tracking of attractive displays yield \(\operatorname{Cov}(A,D)>0\)?
3. When does pollinator limitation favour attraction withdrawal \((A\downarrow,R\uparrow)\), dual insurance \((A\uparrow,R\uparrow)\), or guarded attraction \((A\uparrow,D\uparrow,R\uparrow)\)?
4. Which observables distinguish an attraction–defence trade-off from a shared response to an unmeasured interaction regime?

## 2. Megachile leaf-resource chapter

### Claim hierarchy

The existing analysis estimates an **accessible leaf-trait landscape**:

\[
\text{bee distribution} \times \text{plant distribution} \times \text{plant leaf traits}.
\]

It does not yet estimate realised cutting preference or plant defence effectiveness.

### Layer A: availability

For bee species \(b\) and plant species \(i\), estimate overlap \(O_{bi}\). Define the accessible trait centroid:

\[
\boldsymbol\mu_b=\frac{\sum_i O_{bi}\mathbf x_i}{\sum_i O_{bi}},
\]

where \(\mathbf x_i\) is a standardized leaf-trait vector. Also estimate weighted trait hypervolume \(\mathcal H_b\).

Outputs:

- bee-specific accessible trait centroids;
- trait-niche breadth and overlap;
- sensitivity to SDM algorithm, background choice, occurrence filtering, and trait imputation.

### Layer B: realised use

Build a harmonised interaction table from host records, museum labels, literature, observation platforms, or direct field records. Model use conditional on availability:

\[
\operatorname{logit}\Pr(U_{bi}=1)=
\beta_0+
\beta_1\operatorname{Availability}_{bi}+
\boldsymbol\beta_2^\top\mathbf x_i+
 u_b+v_i.
\]

This is the first point at which leaf traits can be evaluated as conditional selection/avoidance predictors.

### Layer C: interpretation

Separate traits into:

- physical accessibility / cutting cost;
- mechanical resistance proxies;
- resource-acquisition axis;
- chemical-defence proxies, only when actual chemical data are supplied.

Do not label SLA, LDMC, or thickness as defence by default.

## 3. Campanula chapter

Use the separate `campanula-channel-identification` protocol for

\[
W(z)=F(z)E(z).
\]

This repository contributes the trait-architecture framing: attraction traits \(A\), reproductive assurance \(R\), and antagonist-facing traits \(D\). It does not replace the F-versus-E identifiability requirement.

## 4. Cirsium chapter

Candidate trait modules:

- attraction: display size, colour, orientation, nectar;
- defence/access: involucre morphology, spines, sticky secretion, architecture;
- assurance: floral phenology and compatibility-related traits where measurable.

The immediate task is a trait dictionary and an explicit interaction map before any comparative model is fitted.

## 5. Integration standard

Every empirical analysis must state:

1. trait module and biological interpretation;
2. interaction guild and response variable;
3. availability versus realised use distinction;
4. causal claim level;
5. phylogenetic, geographic, sampling, and measurement confounders;
6. what observation would falsify the proposed interpretation.
