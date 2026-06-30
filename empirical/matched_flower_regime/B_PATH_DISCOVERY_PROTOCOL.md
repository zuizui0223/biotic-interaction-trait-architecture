# Sparse-path candidate discovery protocol

## Purpose

The initial four-path evidence map identifies two thin strata that cannot be
advanced by broad all-channel discovery alone:

```text
1. B_flower → floral-antagonism
2. individual A_flower → pollination
```

This protocol adds targeted bibliographic M0 discovery routes for those two
strata. It does not register a study card, trait role, effect estimate, or
causal interpretation.

## B-path discovery rule

A candidate is only a B→antagonism lead when full text can later establish all
of the following:

```text
- a measured or experimentally altered flower-specific resistance/barrier trait;
- a floral-stage antagonist outcome with a defined denominator or exposure;
- a direct trait-to-antagonist estimate or a recoverable raw table that can
  support one under a predeclared model.
```

Floral scent, nectar, pollen reward, damage, or an antagonist count alone are
not treated as B_flower evidence.

## Individual A→pollination discovery rule

A candidate is only an A→pollination lead when full text can later establish:

```text
- a direct floral attraction trait measured on individual plants or flowers;
- an individual-level pollination outcome or declared proxy with exposure;
- a direct trait-to-pollination estimate or a recoverable raw table;
- a common biological unit and compatible sampling context.
```

Population-level visitor assemblages or treatment comparisons without a direct
trait predictor do not qualify.

## Discovery outputs

The OpenAlex harvest may retain title, DOI, OA route, abstract metadata, and
query provenance. Every returned work remains:

```text
M0_candidate_needs_full_text
```

Candidates are screened in public-source availability order, not promoted by
keyword match or citation count.