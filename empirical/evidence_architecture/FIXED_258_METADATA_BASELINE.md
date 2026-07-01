# Fixed 258-work retrieval-metadata baseline

## What this is

This is a descriptive baseline of the immutable PR #20 OpenAlex candidate
snapshot. It is the starting point for the all-258 evidence-architecture audit.

It is **not** a count of studies that measured floral A, floral B, pollination,
floral antagonism, or fitness. Every signal below is retrieval metadata from the
archived candidate snapshot and must be source-verified before it becomes an
evidence-architecture component.

## Corpus composition

```text
candidate works:           258
works with DOI:            256
works without DOI:           2
abstract metadata present: 235
abstract metadata absent:   23
OpenAlex OA route present: 238
OpenAlex OA route absent:   20
```

```text
article:       217
review:         32
preprint:        6
dissertation:    1
letter:          1
book chapter:    1
```

An OA route is not a verified public full-text record. It is only a retrieval
route to be checked at the next source-access stage.

## Archived retrieval signals

| Retrieval signal | Works flagged | Meaning at this stage |
|---|---:|---|
| attraction (`A`) | 118 | title/abstract/search metadata signals an attraction/display topic |
| barrier (`B`) | 36 | metadata signals a barrier/resistance/defence topic |
| pollination (`P`) | 227 | metadata signals a pollination/visitor topic |
| antagonism (`H`) | 44 | metadata signals a floral antagonist/florivory topic |
| recoverability | 20 | metadata signals a possible data or model-recovery route |

The four-signal vectors `(A,B,P,H)` are:

```text
0000:  21       1000:   3       0100:   0       0010: 100       0001:   3
1100:   2       1010:  60       1001:   2       0110:   0       0101:   0
0011:  16       1110:  28       1101:   0       1011:  17       0111:   0
1111:   6
```

Only six works have all four **metadata signals**, but this does not mean six
works measured all four channels. The six include conceptual/review material and
studies later found not to have a directly eligible trait-path estimate.

## Why this baseline matters

The metadata landscape already suggests that pollination language is common in
the fixed retrieval corpus, while barrier and antagonist language is much less
common. This is not yet a biological finding. It is a clear reason to code the
study architectures explicitly rather than treating all 258 as interchangeable
effect-size records.

The all-258 audit will distinguish:

```text
mentioned             -> a topic occurs in source text
measured_indirect     -> an outcome or trait occurs but not as an eligible direct component
measured_direct       -> the study actually measures the declared component
shared-unit eligible  -> components can be joined on the same biological unit/context
four-path eligible    -> all needed components are jointly available under the protocol
```

## Interpretation boundary

No hypothesis test, effect direction, trait role, causal claim, or field-wide
prevalence estimate may use these metadata flags directly. The fixed retrieval
corpus is query-defined, not a random sample of the literature.