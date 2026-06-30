# *Impatiens capensis* four-path observational panel

## Source identity and reproducibility

```text
study id:       Gorden_Adler_2018_Impatiens_capensis
article DOI:    10.1002/ajb2.1182
data DOI:       10.5061/dryad.0j96d17
analysis unit:  individual plant (`Plot_Number`)
source route:   title-validated Dryad version archive
```

The dataset title was matched to the article before accessing the archive. The
archive supplied a processed individual-plant panel and documented raw tables
for floral visitors, natural florivory, flower traits, fruit, and seed outcomes.
No individual observations are committed to this repository.

## Predeclared trait and outcome mapping

```text
A_flower
  Early_Season_Flower_Redness
  percentage of the floral lip that was red-orange in early-season,
  pre-treatment flowers

B_flower
  Early_Season_Condensed_Tannins
  relative condensed tannin measure from early-season, pre-treatment flowers

P
  Pollinators_Per_Hour
  reproductive-organ-contact visits by Bombus/Apis, standardized to 60 minutes

H
  Average_Percent_Florivory
  natural floral tissue missing; supplemental imposed florivory excluded from
  the raw natural-florivory response definition
```

`B_flower` is retained as a **floral chemical barrier candidate**. It was not
itself experimentally manipulated, so every trait-path coefficient below is an
observational association, not a causal tannin-effect estimate.

## Four predeclared directional effects

Each pathway model used standardized predictors/outcome within its declared
complete-case analysis set and HC3 robust standard errors. All models adjusted
for randomized supplemental robbing, florivory, and pollination assignments,
plus `Date_of_First_CH_Flower`.

| Part I path | Trait | Outcome | n | Standardized slope | HC3 SE | 95% CI |
|---|---|---:|---:|---:|---:|---:|
| A_flower → pollination | early flower redness | pollinators/hour | 81 | +0.0079 | 0.1233 | −0.2337, +0.2495 |
| B_flower → pollination | early floral tannins | pollinators/hour | 81 | −0.1807 | 0.1240 | −0.4237, +0.0623 |
| A_flower → floral antagonism | early flower redness | natural florivory | 154 | −0.0948 | 0.0696 | −0.2312, +0.0416 |
| B_flower → floral antagonism | early floral tannins | natural florivory | 154 | +0.0898 | 0.0744 | −0.0560, +0.2357 |

The four confidence intervals overlap zero. The result is therefore **not** a
strong directional sign result for any pathway. Its value is that all four
predeclared arrows are estimable on the same study landscape with separately
measured floral A and B candidates and recoverable individual-level data.

## Fitness-component surfaces

The archive also supports separate observational `A × B` surfaces for two
chasmogamous reproductive components:

```text
CH fruits per plant per day: n = 170
  A × B = −0.0820, HC3 SE = 0.0548, 95% CI [−0.1895, +0.0254]

seeds per CH fruit: n = 85
  A × B = +0.1040, HC3 SE = 0.1043, 95% CI [−0.1005, +0.3086]
```

Neither is a total lifetime reproductive-fitness surface. They therefore do not
upgrade this source to D2, and they do not identify a shared allocation cost
`c_AD` for D3.

## Classification

```text
matched-study structure:  D1_channel_mechanism_candidate
causal status:            observational trait paths, treatment-adjusted
D2 status:                not identified
D3 status:                not identified
parameter bridge:         standardized-slope-ready by scale only;
                          still requires an explicit calibration contract
```

## Interpretation boundary

This source may contribute four **scale-specific observational effect records**
to the broad four-path synthesis. It must not be cited as proof that flower
colour or floral tannins causally alter pollination or florivory, as proof of a
universal A–B trade-off, or as a direct calibration of the shared-cost term.
