# B-to-P precision batch 2: *Toxicoscordion* public repository audit

## Frozen resolver receipt

```text
workflow run:    28500694503
artifact:        8002851071
artifact digest: sha256:1b6a52dfe4a60ad737bf0fabaabff220d6a11a4b4842da0032f5d63382027855
queue rows:      1
resolver status: success
```

## Strict public repository result

| Repository | Resolution |
|---|---|
| DataCite | not found |
| Dryad | not found |
| Zenodo | not found |

```text
receipt count:       3
manifest recovered:  0
landing page only:   0
access failed:       0
not found:           3
```

The resolver found no article-linked public data manifest under its strict
identity contract:

```text
DataCite exact declared relation
Dryad explicit study DOI or exact linked Dryad DOI
Zenodo IsSupplementTo / IsDerivedFrom / IsPartOf
```

## Interpretation

*Toxicoscordion* remains an abstract-resolution, direction-only B-to-P record.
This does not imply that publisher-hosted supplementary material, author-held
files, or another non-screened archive does not exist. It means that the
screened public repository routes did not expose an eligible article-linked
manifest at the frozen run.

No numerical effect is extracted, and the record cannot enter a quantitative
mini-meta-analysis.