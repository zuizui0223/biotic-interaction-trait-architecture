# B-to-P precision batch 1: public source audit protocol

## Objective

Attempt numerical-effect recovery for the four direct abstract-level records:

```text
B_to_pollination
  - Gelsemium defensive nectar alkaloid -> bumblebee behavior
  - nicotine in artificial nectar -> bird foraging
  - Delphinium nectar alkaloid -> bumblebee visits/time per flower

B_to_antagonism
  - Petunia defensive floral volatile blend -> florivory/damage
```

## Public repository resolution

The automated receipt search uses only documented public metadata endpoints:

```text
DataCite
Dryad
Zenodo
preverified Mendeley handles only
```

A result is accepted as a candidate file manifest only when article-to-dataset
identity passes the existing strict contract:

```text
DataCite: exact study DOI in a declared relation
Dryad: exact study DOI or exact DataCite-linked Dryad DOI in response
Zenodo: exact study DOI with IsSupplementTo, IsDerivedFrom, or IsPartOf
```

A citation-only Zenodo relation does not qualify.

## Extractability states after resolution

```text
M0_public_source_unavailable
    no eligible public manifest/table found

M0_public_manifest_needs_inspection
    article-linked manifest found; file contents not yet screened

M1_direction_only
    source supports an oriented direct route but lacks a compatible estimate
    and uncertainty or raw reconstruction fields

M1_quantitative_candidate
    source contains route-compatible table/raw fields; extract only after
    checking units, denominator/exposure, orientation, and shared panel ID
```

## Prohibitions

```text
- No publisher abstract is converted into a numerical effect.
- No search-result snippet becomes a source locator.
- No dataset merely citing a paper is treated as its supplementary data.
- No feeder-choice assay is pooled with flower-visitation data.
- No natural-range and supra-natural dose effects are averaged without a
  predeclared dose scale and compatible design.
```

## Expected product

The source audit is successful even if all four studies remain M1 direction-only
or M0 inaccessible. The result then documents exactly why a B-to-P mini-meta-
analysis cannot yet be run.