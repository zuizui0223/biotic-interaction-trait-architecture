# Kellenberger et al. (2019) — *Gymnadenia rhellicani* source screen

```text
article DOI:       10.1038/s41467-018-07936-x
public source DOI: 10.6084/m9.figshare.7314731.v10
source status:      article-declared Figshare package verified
screen status:      header recovered; image exposure mapping unresolved
```

## Provenance contract

The article's public Data Availability statement explicitly names Figshare
accession `7314731` for the remaining generated and analysed datasets. The
Figshare API returned the same accession and a machine-readable manifest.

```text
article-declared accession: 7314731
Figshare accession returned: 7314731
manifest recovered:          yes
```

This is a verified public source route. It does not by itself establish a
trait-to-outcome effect.

## What the package structure establishes

The small-datasets workbook contains a `plots_Puflatsch` sheet with headers for
one focal plant/plot record including:

```text
sample, population, plot, morph,
flowers_visible, flowers_total,
herbivory_2015, capsules_visible, capsules_total,
seeds_scored, seeds_prop_viable, fitness,
reflower_2016, colour_2016, herbivory_2016
```

Thus floral morph and several reproductive / floral-antagonism outcomes occur
in a recoverable individual-plant data structure. They must not be repurposed
as a direct pollination outcome without an explicit bridge.

## Pollinator-image manifest audit

The package contains five declared pollinator-recording archives. A central-
directory-only audit did not read image pixels or image paths.

```text
2016 archive 1: 8,155 JPG files; no black/red/white or timestamp filename tokens
2016 archive 2: 8,675 JPG files; no black/red/white or timestamp filename tokens
2017 archive 1: 8,848 JPG files plus 10 AVI files; no black/red/white or timestamp filename tokens
2016 archive 3: ZIP central-directory manifest unavailable
2017 archive 2: ZIP central-directory manifest unavailable
```

The absence of morph and timestamp tokens in the readable archive names means
that image filenames alone cannot establish morph-specific display exposure or
observation duration. The inaccessible central directories cannot fill that gap.
No image content was downloaded or inspected by this audit.

## Current evidence boundary

```text
source route:              verified
individual morph + fitness: header-level recoverable
individual morph + visit rate: not extracted
camera exposure mapping:    unresolved from public filenames
A_to_pollination effect:    not registered
B_flower module:            not identified
D1 / D2 / D3:               not established
```

Fruit, seed, and fitness columns cannot be substituted for an individual
pollination outcome. A future image-derived visit record must first define its
observation unit, image exposure, landing criterion, visitor coding rule, and
mapping between camera treatment and floral morph.

## Next gate

Follow `GYMNADENIA_RHELLICANI_POLLINATOR_ANNOTATION_PROTOCOL.md` before opening
or counting any camera frames. The protocol must be satisfied separately for
the 2016 in-situ paired-morph design and the 2017 cut-inflorescence triplet
design; these are not pooled automatically.

The first remaining source requirement is a camera-layout or experimental
mapping record that links each camera sequence to its displayed morph(es) and
observation interval. Without it, no colour-morph visitation effect can be
computed transparently from these archives.