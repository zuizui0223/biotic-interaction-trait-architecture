# Matched-study protocol for direct floral regime tests

## Why the route changes here

The public global-join route has now been assessed and retired for the first
empirical test:

```text
Web of Life × BIEN leaf traits  → insufficient provider-row coverage
GloBI plant–antagonist claims   → not a sampled-network backbone
TRY custom export               → not a reproducible active dependency
```

The replacement is not a smaller, less rigorous version of the same join. It is
a different evidential design: **studies are the unit of integration**. A study
is eligible only when it records the relevant flower traits and both biotic
interaction channels in the same biological context.

## Link to Part I

Part I derives the exact local relation for the current score:

```text
A_flower × B_flower
```

where attraction/access and floral barriers/resistance may be locally
complementary, substitutable, or neutral depending on floral-antagonist tracking,
barrier efficacy, pollinator-access obstruction, reproductive assurance, and
shared cost.

The direct empirical question is therefore not a generic correlation between two
traits. It is:

> Within a declared plant–site–time context, are **separately measured**
> attraction and floral-barrier traits associated with pollination and
> floral-antagonist observations in a way compatible with a preregistered Part I
> scenario?

## Evidence products

| Product | Minimum matched information | Permitted output |
|---|---|---|
| **M0: candidate card** | bibliographic record plus an explicit reason it may contain flower traits, pollination, and floral antagonism | search / acquisition priority only |
| **M1: channel ledger** | a direct floral trait plus either pollination or floral-antagonist observation, with site or study identity | one-channel descriptive evidence |
| **M2: aligned two-channel panel** | attraction and floral-barrier traits plus pollination and floral-antagonist observations in same study landscape and overlapping time | component-level joint association; may include a biologically meaningful A/B composite, but cannot identify the Part I mixed relation from that composite alone |
| **D1: direct regime panel** | M2 plus separately measured A_flower and B_flower modules, plant-level (or predefined population-level) linkage, compatible denominators, explicit trait methods, and recoverable table/repository | compatible / contradicts / not identified for a declared Part I observation model |

A paper title, a review statement, or separate datasets joined by taxon name alone
never exceeds M0.

## Non-negotiable matching rules

A D1 candidate must document all of the following:

```text
1. Floral attraction trait(s)
   e.g. display, flower/capitulum size, floral scent, reward, colour contrast,
   orientation, access geometry.

2. Floral barrier/resistance trait(s)
   e.g. floral chemical defence, structural protection, trichomes/spines,
   toughness, access limitation, or a separately justified flower-specific
   barrier mechanism.

3. Module separation
   A_flower and B_flower must be measured as independently variable modules.
   A single composite that combines showiness/access and protection cannot test
   their A_flower × B_flower relation: its change may arise from either module.
   Such a study can be M2, not D1.

4. Pollination channel
   e.g. visitation with observation denominator, pollen transfer, pollinator
   effectiveness, outcrossing proxy, or reproductive response tied to visitation.

5. Floral antagonist channel
   e.g. florivory, flower damage, seed predation, nectar robbery, pollen theft,
   or an explicitly flower-attacking antagonist, with a denominator.

6. Alignment
   same study landscape plus exact or predeclared-overlap site/time alignment.

7. Linkage
   the unit carrying the traits can be linked to both channels at individual,
   plant-population, patch, or network level. The linkage level is declared and
   never silently upgraded.

8. Recoverability
   raw or machine-readable table, supplement, repository data, or a clearly
   defined digitised aggregate. Narrative statements alone do not qualify.
```

## What belongs outside this route

- leaf traits and leaf herbivory without a stated cross-organ bridge;
- broad pollination syndromes, because they encode the process being explained;
- interaction claims pooled across studies without study-specific sampling;
- floral traits and florivory measured in different years/sites without a
  declared alignment model;
- global taxon joins using trait imputations as though they were observations.

## Study-card workflow

1. Register a candidate as M0 from a reproducible seed query, citation chase,
   repository search, or known study.
2. Read full text and supplement before assigning any channel status.
3. Record trait definition, whether A and B are independently measured,
   interaction response, denominator, unit of linkage, site, time, and raw-table
   status.
4. Run `examples/audit_matched_flower_studies.py`.
5. Acquire data in this order:

   ```text
   supplement / repository
   → machine-readable appendix
   → author-provided table
   → aggregate figure digitisation (only descriptive or explicitly aggregate)
   → exclude
   ```

6. Freeze the registry before modelling. Do not add studies after seeing a
   pooled sign unless the addition follows the predeclared search/citation route.

## Route expansion rule

Screen 15 high-information M0 candidates from each of three seed routes:

```text
A. floral-trait × florivory / flower-damage studies
B. floral-scent or reward × pollinator + antagonist studies
C. pollination / florivory / seed-predation studies with plant-level tables
```

A candidate is high-information only when metadata or full text indicates at
least one of: a trait table, visitor counts, floral-damage counts, seed-predation
counts, individual/plant identifiers, a stated site-period, or an accessible
supplement/repository.

After each 15-card block:

- **>= 3 D1 or M2 cards:** expand that route and retrieve tables;
- **1–2 D1 or M2 cards:** retain as a secondary route and citation-chase;
- **0 D1/M2 but >= 3 M1 cards:** retain as a descriptive mechanism ledger;
- **0 useful cards:** stop that route.

## Interpretation categories

A D1 result can be labelled only as:

```text
compatible_with_declared_scenario
contradicts_declared_scenario
not_identified
```

`not_identified` is the correct result when any required trait, module
separation, denominator, alignment, or linkage is absent. It is not evidence for
absence of a floral trade-off or complementarity.
