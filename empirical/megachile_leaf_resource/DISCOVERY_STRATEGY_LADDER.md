# Discovery strategy ladder: maximize usable plant records, not hits

## Core distinction

Genus-level search is **rational for discovery**, but not for the final trait analysis.

\[
\text{genus-level query} \rightarrow \text{candidate action record}
\]

\[
\text{species-identified bee + species-identified plant} \rightarrow \text{trait-analysis record}
\]

The purpose of broad search is to find the best sources and direct-action pages. Taxonomic resolution is upgraded afterwards where possible.

## Pilot comparison so far

| Discovery route | Search unit | Direct material-action yield | Plant-ID yield | Decision |
|---|---|---:|---:|---|
| exact species + English nesting terms | named *Megachile* species | very low in the first pilot | none recovered | retain only as follow-up |
| species pages in a structured Japanese natural-history source | named Japanese species | 2 direct leaf-action records in 4 checked pages | 1 genus-level plant record | useful for material-mode classification |
| broad genus text search (`Megachile` / `ハキリバチ` + leaf-cutting terms) | genus/common name | poor; results dominated by generic biology or unrelated wasps | no usable Japanese plant record in the checked result set | do not scale as plain web-text search |
| broad genus image/observation search | genus/common name + direct-action words | direct cutting candidates appeared | plant identity sometimes visible/mentioned, but requires review | next candidate for scalable discovery |

This is not a comparison of total internet coverage. It is a small yield test that determines the next source class to test.

## Working strategy

### Stage A — high-recall discovery

Search at genus/common-name level, but only with **action words**:

```text
ハキリバチ 葉を切る
ハキリバチ 葉を運ぶ
ハキリバチ 葉片 巣材
Megachile cutting leaf
Megachile carrying leaf
Megachile nest material leaf
```

Search sources are ranked by whether they provide original images, observation date, location, and a stable source page. Generic advice pages and reposts are discarded.

### Stage B — source-first expansion

Once a source produces one credible action record, search *within that source* for its own action vocabulary and Megachile tags. This is more efficient than repeating unrestricted web searches.

### Stage C — resolution upgrade

For every candidate record:

1. verify material action;
2. reconcile the bee identification;
3. identify the plant from source text, image, or uploader follow-up;
4. retain unresolved records in the material-action ledger;
5. promote only taxonomically resolved bee--plant records into the trait universe.

## Pivot triggers

For each source class, process a fixed first batch of 20 candidates and report:

\[
Y_{\rm action}=\frac{n_{\rm direct\ action}}{n_{\rm candidates}},\qquad
Y_{\rm plant}=\frac{n_{\rm plant\ identified}}{n_{\rm direct\ action}},\qquad
Y_{\rm trait}=\frac{n_{\rm species\ ready}}{n_{\rm candidates}}.
\]

- If \(Y_{\rm action}=0\), abandon that source class.
- If action records exist but \(Y_{\rm plant}=0\), keep it only for material-mode classification and move plant discovery elsewhere.
- If \(Y_{\rm trait}>0\), expand until at least 30 independent bee--plant records or the source is exhausted.

## Next test

Test a photo/observation source where image pages have taxon labels and stable observation metadata. Compare its 20-candidate yield against the structured natural-history species-page source.

The current goal is not to prove a host preference. It is to identify the discovery route that can deliver enough verified bee--plant material-use records for any later trait analysis.
