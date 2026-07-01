# B-to-P precision batch 1: public repository source audit

## Frozen resolver receipt

```text
workflow run:    28499410653
artifact:        8002337732
artifact digest: sha256:6fd0746a9dbe9d87ba772305b96d4a3f9e73e6ed7d58c752802e16216a403e6d
queue rows:      4
resolver status: success
```

The source resolver queried the documented public metadata endpoints for each
focal study DOI:

```text
DataCite
Dryad
Zenodo
```

## Result

| Study | DataCite | Dryad | Zenodo | Eligible public manifest |
|---|---|---|---|---|
| *Gelsemium sempervirens* defensive nectar alkaloid | not found | not found | not found | no |
| bird nicotine tolerance | not found | not found | not found | no |
| *Delphinium barbeyi* nectar alkaloids | not found | not found | not found | no |
| *Petunia* defensive floral volatile blend | not found | not found | not found | no |

```text
receipts:             12
manifest_recovered:    0
landing_page_only:     0
access_failed:         0
not_found:            12
```

## Interpretation

All four records remain **direction-only, abstract-resolution candidates**. No
public repository table or raw dataset can currently be inspected through the
strict resolver routes, so no numerical effect is extracted.

This audit does **not** establish that no supplementary table, author-held
archive, or publisher-hosted supplement exists. It establishes only that the
screened public repository routes did not expose an eligible article-linked
manifest at the time of the frozen run.

## Consequence for the mini-meta-analysis

```text
B_to_pollination quantitative effects: 0
B_to_antagonism quantitative effects:  0
pooled B-to-P estimate:                not run
```

The three B-to-P records and one B-to-H record remain useful in the broad
direction map. They cannot enter a compatible random-effects effect-size stratum
until a source supplies a direct estimate plus uncertainty or reconstructable
raw inputs, with a clear unit, dose definition, and independent study panel.