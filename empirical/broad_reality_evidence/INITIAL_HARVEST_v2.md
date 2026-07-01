# Initial broad real-world evidence harvest v2

## Retrieval receipt

```text
source:                  Crossref REST API
query routes:            21
requested depth:         200 journal-article records per query
raw returned records:    4,183
unique DOI/title records: 2,896
records with abstract metadata: 1,008
```

This is deliberately larger than the fixed 258-work OpenAlex snapshot. The two
corpora have different roles and must not be silently combined.

```text
fixed_258_OpenAlex_v1
    immutable, reproducible study-design/identifiability audit

broad_reality_evidence_v2_Crossref_seed
    high-recall real-world evidence discovery and shallow source-coding universe
```

## Route coverage in the raw corpus

A record can occur in more than one route because source query membership is
retained rather than arbitrarily assigned.

```text
A_to_pollination:  919
A_to_antagonism:   584
B_to_antagonism:   605
B_to_pollination:  392
joint_channels:  1,078
```

These counts are **query-route memberships**, not counts of studies that
measured or supported the corresponding biological pathway.

## Why a second shallow screen is necessary

Crossref bibliographic queries correctly increase recall but also retrieve
non-biological uses of terms such as "flower", "pollination", or "trichome".
Examples include optimization algorithms, flower-like catalysts, and clinical
or human reproductive records.

A deterministic metadata screen therefore retains the raw corpus and labels
records as:

```text
priority_for_shallow_source_coding
biological_context_needs_route_screen
metadata_context_uncertain
likely_nonbiological_retrieval_noise
```

The priority class needs all of:

```text
- at least two biological flower-context terms in title/container metadata;
- an A or B metadata trait signal;
- a P, H, or W metadata outcome signal;
- no obvious non-biological exclusion term.
```

On the initial harvest this rule selected **650** priority records. This is a
triage set, not a final eligible-study set and not a collection of effect sizes.

## Next analysis layer

The 650-record priority cohort is used for shallow source coding:

```text
study × route × trait class × outcome class
reported sign: positive / negative / mixed / null / not reported
observational / manipulation / comparative / review
accessibility and quantitative-effect availability
```

Only later, separately, are compatible numerical effect strata pooled. The
initial broad corpus is already useful even if many records stop at sign or
design coding: it maps real-world support, contradiction, and missing channels
against the Part I robustness map.