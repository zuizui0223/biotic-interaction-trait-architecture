# Broad real-world evidence protocol

## Role in the project

The scientific hierarchy is:

```text
Part I  mathematical robustness and sensitivity analysis
Part II broad literature evidence: real-world support, contradiction, and gap structure
Part III strict four-path records: high-quality calibration anchors only
Part IV self-contained field data: direct D1/D2 tests where the literature is structurally incomplete
```

The broad literature corpus does **not** calibrate the Part I model coefficient
by coefficient. It asks a more appropriate empirical question:

> Across diverse flower systems, do published studies provide real-world evidence
> that is directionally compatible with, contradictory to, or silent about each
> interaction channel predicted by the robustness map?

## Why this corpus is broad

A study need not jointly measure A, B, P, H, and W to be useful here.

```text
A_to_pollination  -> flower colour, size, display, scent, or rewards with visitation/pollen/fitness
A_to_antagonism   -> floral attraction/display traits with florivory, damage, robbery, or predation
B_to_antagonism   -> flower-specific resistance/access traits with floral antagonism
B_to_pollination  -> flower-specific resistance/access traits with pollination outcomes
joint_channels    -> pollination and antagonism jointly considered, with or without fitness
```

The strict registry continues to require direct floral traits, declared roles,
denominators/exposure, uncertainty, and compatible unit/context before an effect
is used as a quantitative high-quality anchor. The broad corpus has a different
job and is never discarded because those criteria are absent.

## Corpus v2 retrieval

```text
source: Crossref REST API
work type: journal-article
query families: 21 independent high-recall queries
routes: A_to_pollination, A_to_antagonism, B_to_antagonism, B_to_pollination, joint_channels
per-query depth: predeclared and reported in the retrieval receipt
identity rule: normalised DOI; title-year hash only when DOI is unavailable
```

The fixed 258-work OpenAlex snapshot remains unchanged and supports its own
reproducible design-architecture audit. Corpus v2 is a separate retrieval
universe for broad real-world evidence synthesis.

## Three evidence resolutions

### Resolution 0: bibliographic discovery

All deduplicated records contribute:

```text
query membership
route family
work type/year/source metadata
metadata text signals for A, B, P, H, W
```

These are retrieval and triage facts only.

### Resolution 1: shallow source coding

For all eligible primary studies with usable abstract/full text, code:

```text
study system and taxon
route family or families
trait class
outcome class
reported sign: positive / negative / mixed / null / not reported
study design: observational / manipulation / comparative / review
source accessibility
```

The coding unit is `study × route × trait class × outcome class`, not a claim
that all routes were measured on one biological unit.

### Resolution 2: compatible quantitative strata

Extract a numerical effect only when a study reports or permits recovery of a
known effect type. Pooling is allowed only within predeclared compatible strata,
for example:

```text
flower colour -> pollinator visitation: log response ratio
flower colour -> floral damage: odds ratio
floral defence treatment -> florivory: log response ratio
flower trait -> fruit set: standardised regression coefficient
```

Do not pool across different outcomes, trait roles, scales, or causal designs.
When a stratum has too few compatible estimates, use directional evidence maps,
sign counts with design qualifiers, and evidence-gap plots instead of a fake
meta-analytic mean.

## Main empirical outputs

```text
1. Coverage map: how many study-route records exist for A→P, A→H, B→H, B→P, and joint channels?
2. Direction map: where do reported signs align with or contradict Part I's conditional regime predictions?
3. Design map: observational versus manipulation and outcome/trait class coverage.
4. Quantitative mini-meta-analyses: only for compatible effect strata with enough independent studies.
5. Gap map: which predicted channels are empirically sparse, mixed, or inaccessible?
```

## Interpretation boundaries

```text
- Query membership is not evidence of measurement.
- Text signals are not effect directions.
- Sign coding is not causal inference.
- Broad-study counts are not global prevalence estimates; they describe the versioned retrieval corpus.
- A contradiction in one trait/outcome context does not refute a conditional model; it identifies a regime or trait-role boundary to model.
- Strict D1/D2 records remain the only route for direct parameter anchoring.
```

## Decision rule

The broad corpus is successful if it yields a transparent, high-recall map of
real-world support and contradiction, even if most studies cannot enter a common
effect-size model. The goal is not to force every paper into one coefficient.
