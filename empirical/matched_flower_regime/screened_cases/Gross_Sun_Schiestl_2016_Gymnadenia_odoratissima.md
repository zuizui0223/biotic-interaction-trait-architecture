# Gross, Sun & Schiestl (2016) — *Gymnadenia odoratissima* exact Dryad audit

```text
article DOI:       10.1371/journal.pone.0147975
public dataset DOI:10.5061/dryad.dj40r
package title:      Data from: Why do floral perfumes become different?
                    Region-specific selection on floral scent in a terrestrial orchid
archive status:     9-file manifest; 8 table headers recovered
```

## Provenance status

The article declares the Dryad DOI in its public Data Availability statement,
and the Dryad package title begins with `Data from:` followed by the matching
study title. DataCite records the article with the relation type `IsCitedBy`,
which is not a qualifying supplement/derivation relation under the repository's
strict relation-only rule.

```text
article-declared dataset DOI:          yes
matching Data from: title:              yes
DataCite qualifying relation:           no (IsCitedBy)
current identity status:                title-validated, relation-type pending
```

The article-declared DOI plus matching package title is sufficient for a
transparent, written provenance contract. It is not silently relabelled as a
relation-only verified supplement.

## Header-level evidence

Individual `PlantID`, `Year`, `Region`, `Population`, and `NrFlowers` fields
recur across key tables:

```text
FloralTraitDifferences
  → individual scent compounds, total scent, flower number, display traits

HerbivoryDifferences
  → PlantID, NrFlowersEaten, AphidLoad

ReproductiveSuccessDifferences / SelectionAnalysis
  → PlantID, NrFlowers, NrFruits, proportional or relative female success

PollinatorLimitation
  → PlantID, treatment, NrFlowers, NrFruits, proportional female success

PollinatorFamiliesPerH / NoPollinators_PollinatorFamilyRichness
  → population-date pollinator observations, not individual-plant outcomes
```

## Row-linkage and timing audit

The no-row audit retained aggregate counts only. It found:

```text
floral-trait rows with complete PlantID + Year + Region + Population key: 1,162
one-to-one floral-trait ↔ herbivory keys:                                 1,162
one-to-one floral-trait ↔ reproductive-success keys:                      1,028
linked flower-eaten records with positive numeric flower denominator:     1,162
linked records with eaten flowers > flower count:                              0
linked records with missing/nonpositive numeric contract:                     0
```

The article methods report that all individual plants were marked when in full
flower, flower number and floral signals were measured then, and floral
herbivory was quantified for all marked plants **on the day floral signals were
measured**. The herbivory variable is the number of eaten flowers per
inflorescence. Thus the individual link and available flower-count denominator
are aligned at the field-observation level.

## Registered A→floral-antagonism effect

One model was declared before inspecting the estimate:

```text
trait:       total floral scent amount, log1p then standardized
outcome:     eaten flowers out of total flowers per inflorescence
model:       binomial logit, population × year fixed intercepts
uncertainty: conservative quasi-binomial SE
causal role: observational association only
```

```text
complete linked individuals: 1,162
population-year strata:       13
log odds ratio per 1 SD scent: +0.568
95% CI:                        +0.042 to +1.094
two-sided p-value:             0.034
Pearson dispersion:            8.386
```

Thus, conditional on population × year, individuals with higher total floral
scent had higher same-day odds of flowers being eaten. The record is retained as
`A_to_antagonism` on its reported log-odds scale. The dispersion-adjusted
standard error is deliberately conservative.

## Interpretation boundary

The positive association does **not** show that scent causally attracts
antagonists, that scent is a defence trait, or that floral herbivory selected for
or against scent. Trait and herbivory were measured on the same day, and the
analysis is observational. The reported log odds ratio is kept
`scale_specific_only`; it is not inserted directly into the Part I parameter
envelope.

The archive still does **not** supply an individual `A_to_pollination` effect,
because observed pollinator measures are population-date outcomes. No
independently justified `B_flower` trait is present.

## Current classification

```text
status:             M1 individual A-to-antagonism evidence
registered effect:  Gross_Sun_Schiestl_2016_Gymnadenia_A_to_H_total_scent
not established:     B_flower module, individual A_to_pollination, D1/D2/D3
```