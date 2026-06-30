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

## What this can support next

A predeclared observational `A_to_antagonism` model is now possible for a floral
attraction candidate such as standardized log total-scent amount, using eaten
flowers out of total flowers as the floral-antagonism outcome and controlling
for population and year. This must be reported as a conditional observational
association, not causal floral-scent defence or adaptation.

The archive still does **not** supply an individual `A_to_pollination` effect,
because observed pollinator measures are population-date outcomes. No
independently justified `B_flower` trait is present.

## Current classification

```text
status:             high-information individual A-to-antagonism panel
eligible next step:  predeclared observational A_to_antagonism extraction
not established:     B_flower module, individual A_to_pollination, D1/D2/D3
four-path registry:  no effect registered yet
```
