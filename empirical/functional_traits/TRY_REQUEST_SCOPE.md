# TRY request scope — optional infrastructure, not the active plan

## Status

**Do not submit a TRY request as a dependency of the current project.**

The repository contains a request manifest, receipt template, and coverage audit
because they are useful provenance infrastructure if a collaborator later
supplies an authorised export. They are not an operational path for the first
empirical analysis: a custom TRY request and manual download cannot be required
for a reproducible, scalable workflow.

## Active rule

```text
No manual, one-off trait request
→ no dependency in the active global-analysis route.
```

Only publicly accessible sources that can be retrieved again by code may advance
to the automated feasibility stage. A source still has to pass the trait-specific
direct-record and network-metadata coverage gates after it is retrieved.

## What the retained files are for

- `scripts/prepare_try_wol_request.py`: preserves a reproducible taxon manifest
  for a possible future data-use agreement; it is not a current deliverable.
- `trait_receipt_template.csv` and `TRAIT_RECEIPT_CONTRACT.md`: preserve
  record-level provenance if any authorised trait export is received.
- `audit_trait_receipt_coverage.py`: remains usable for any source, not only
  TRY, after its records are normalised into the contract.

## Public-data-first trait priorities

The initial automated feasibility screen, when an eligible public source is
available, focuses on leaf functional traits because they have a clearer
cross-taxon measurement tradition than floral traits:

```text
SLA or LMA
LDMC
leaf nitrogen concentration
leaf phosphorus concentration
leaf thickness
```

These are `Q_leaf` traits: construction and resource-quality variables, not a
claim that they are direct defence traits. Mechanical and chemical resistance
traits remain conditional because units, methods, and compound definitions must
be comparable.

## Floral traits

No current public global provider has been retained as an automated floral-trait
backbone for the Web of Life plant set. Flower size, display, reward, colour, and
access traits can therefore enter only through a **matched-study** route: the
same study must supply both pollination edges and measured floral traits. They
must not be backfilled manually across thousands of taxa.

## What not to do

- do not clean or submit the 3,107-name TRY manifest now;
- do not use a custom trait export as the first empirical milestone;
- do not replace direct records with gap-filled values in a primary analysis;
- do not claim that a trait source is adequate before the automated coverage
  screen passes.
