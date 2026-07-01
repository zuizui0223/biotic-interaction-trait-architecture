# OpenAlex retrieval-scope audit: fixed 258 versus current discovery head

## Why audit retrieval scope

The fixed 258-work corpus is a reproducible historical snapshot, not proof that
only 258 relevant works exist. It was created by six OpenAlex free-text searches
with `--results-per-query 50`, then deduplicated by OpenAlex work ID.

```text
historical query IDs: A01, A02, B01, B02, C01, C02
historical OpenAlex head: 50 results per query
maximum raw results: 300
unique deduplicated works: 258
```

The same query registry also contains `D01`–`D04`, which directly target D1/D2/D3
study designs but were not part of the historical fixed snapshot.

## Audit question

```text
Does the current OpenAlex head show that the historical 50-result cutoff and the
omission of D01–D04 materially limited discovery breadth?
```

OpenAlex's current API allows at most 100 results per response. The first audit
therefore uses a single 100-result response per query, then treats its ordered
first 50 as the comparable head and records rank 51–100 separately. It also
records the API's full result count to determine whether a later cursor-paged
expansion is needed.

The audit compares, using the *current* OpenAlex index:

```text
historical six queries: top 50 versus top 100
D01–D04 routes:         top 50 and top 100
historical snapshot:     overlap with current historical-query results
```

## Outputs

```text
openalex_scope_query_report.csv
    per-query current result count, returned top-50/top-100 counts, rank-51–100
    additions, and whether the API reports more than 100 results.

openalex_scope_candidates.csv
    current bibliographic candidates with query IDs, seed routes, and retrieval
    stratum only. No biological evidence fields are inferred.

openalex_scope_summary.json
    current retrieval-depth and historical-snapshot overlap summaries.
```

## Interpretation rules

- The historical 258-work artifact remains immutable.
- Current OpenAlex differences can reflect both a deeper cutoff and index/ranking
  changes since the original harvest; the audit reports both rather than
  attributing all differences to depth.
- The audit does not make a new corpus automatically.
- The audit does not evaluate full text, traits, outcomes, shared units,
  denominators, effect directions, or evidence levels.
- A later expanded corpus must be assigned a new version, retain every query,
  timestamp, API result count, and deduplication rule, and must never be merged
  silently into the fixed 258-work corpus.

## Decision rules after the audit

```text
If rank 51–100 adds material unique candidate coverage:
    create an explicitly versioned expansion corpus using a declared cursor or
    page-depth rule.

If D01–D04 add material non-overlapping coverage:
    include those routes in the proposed expansion corpus, subject to a separate
    retrieval protocol.

If one or more API meta-counts exceed 100:
    do not call top-100 exhaustive; predeclare cursor paging or a relevance-depth
    cutoff before building an expanded corpus.

If current top-50 has limited overlap with the fixed snapshot:
    report OpenAlex temporal/ranking drift and retain the fixed snapshot for
    all reproducible 258-work analyses.
```

The result determines whether retrieval breadth should be expanded. It does not
change the all-258 evidence-architecture audit already tied to the fixed
historical snapshot.