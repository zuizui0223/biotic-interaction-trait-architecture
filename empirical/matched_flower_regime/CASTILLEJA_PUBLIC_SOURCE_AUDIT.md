# *Castilleja linariaefolia* public-only source audit

## Focal article

```text
DOI:   10.1111/j.0030-1299.2004.12641.x
Title: Direct and indirect effects of pollinators and seed predators to
       selection on plant and floral traits
```

The article remains a high-information bibliographic candidate because its
metadata describes pollination and pre-dispersal seed predation as selection
agents acting on plant and floral traits. That bibliographic information is not
a recoverable effect estimate.

## Public-source audit result

| Route | Result | Interpretation |
|---|---|---|
| Crossref exact DOI | Article metadata and two Wiley content links recovered | Source identity is confirmed; metadata is not full text. |
| OpenAlex exact DOI | No public full-text location returned | No OA PDF route was identified by this endpoint. |
| Wiley TDM endpoint | HTTP 400: client token required | Not publicly retrievable by the reproducible unauthenticated workflow. |
| Wiley direct PDF endpoint | HTTP 403 | Not publicly retrievable by the reproducible unauthenticated workflow. |
| Dryad search candidate `114507` | Resolved to `10.5061/dryad.hx3ffbgkx`, *Data and Code from: Sheltered or suppressed? Tree regeneration in unmanaged European forests* | Unrelated false-positive candidate; excluded. |
| DataCite and Zenodo searches | No study-linked record recovered | No public data route identified by these endpoints. |

## Classification after public-only audit

```text
M0_bibliographic_candidate_public_sources_inaccessible
```

No public full text, article table, supplement, or verified related data package
was recovered. Therefore the following are all **not identified**:

```text
A_flower trait definition and measurement method
B_flower trait definition and measurement method
pollination denominator and response scale
seed-predation denominator and response scale
reported path coefficients and uncertainty
individual/population linkage
```

No effect record is entered into `four_path_effect_registry.csv`. The study is
not promoted to M1, M2, D1, D2, or D3.

## Next decision

Do not request author data at this stage. Continue the public-only screen of the
remaining candidate universe. Reconsider author contact only after that public
screen yields zero usable direct-regime sources and this study remains a leading
candidate.
