# B-flower mechanism-aware full-text triage v1

## Purpose

The floral trait--animal response queue contains 1,318 fixed-corpus candidates.
A simple abstract-level tiering under-ranks B-flower studies because many floral
chemical and structural mechanisms do not advertise generic statistical keywords
in their abstracts.

This protocol changes **reading order only**. It does not expand the corpus,
change inclusion criteria, convert abstract scores into evidence grades, or make
a biological claim from the rank.

## Batch 1 design

```text
B_to_antagonist:
    census every candidate abstract

B_to_pollinator:
    add up to 24 non-census records with the strongest abstract signals of a
    flower-specific barrier/deterrence mechanism plus animal-response language
```

A candidate belonging to both routes is included once in the B-to-antagonist
census. The expected Batch 1 size is therefore no more than 56 unique abstracts,
not 32 + 24 independent study effects.

## Mechanism cues used only for ranking

Positive ranking signals:

- nectar alkaloids, nicotine, caffeine, cardenolides, toxins, or other secondary
  metabolites;
- floral chemical deterrence or repellence;
- floral trichomes, sticky/slippery surfaces, bracts, spines, closures, or other
  physical access barriers;
- explicit defence, deterrence, repellence, cheating, robbery, or access language;
- pollinator or floral-antagonist outcome language;
- empirical/nonreview status and abstract cues of experiment, choice, association,
  or statistics.

Manual false-positive checks lower rank but never auto-exclude a candidate:

- reproductive isolation, hybridization, or post-pollination compatibility;
- molecular/biosynthetic work without a stated animal response;
- generic pollination ecology, pollination syndrome, or network context.

## Full-text screen

For every Batch 1 work, record:

```text
full_text_access
full_text_b_flower_plausible
full_text_b_mechanism
full_text_animal_response
full_text_design
full_text_effect_recoverable
full_text_include
full_text_exclusion_reason
source_locator
```

A work becomes an included effect only under the main synthesis protocol:
flower-organ B, pollinator or floral-antagonist response, recoverable effect size
and variance, and a declared independent study identity.

## Interpretation boundary

The B-to-antagonist census is intentional: the route is sparse enough that
ranking would obscure missingness. The B-to-pollinator top-up improves efficiency
but must never be reported as a random sample, prevalence estimate, or evidence
that remaining candidates are irrelevant.
