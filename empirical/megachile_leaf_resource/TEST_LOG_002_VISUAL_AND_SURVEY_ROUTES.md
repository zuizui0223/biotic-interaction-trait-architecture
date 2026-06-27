# Test log 002 — visual discovery and published-survey routes

## Question

Can either broad visual discovery or existing community-scale leaf-cut surveys provide enough taxonomically resolved plant-use records for a trait analysis?

## Test A: visual/search discovery

### Procedure

Ran two broad image searches:

```text
ハキリバチ 葉を切る 観察 写真
Megachile cutting leaf observation photo plant
```

### Result

The first result page contained many images with a visually plausible direct cutting action. However, the candidate pages were heterogeneous: government field guides, generic explanatory pages, blogs, image repositories, and regional natural-history pages. In most candidates, either the plant was unnamed, the bee was only genus/family-level, or both.

### Decision

**Fail as a primary trait-data route.** It has high action recall but low verified bee-species × plant-species yield and no consistent bulk-download/metadata structure.

Retain only as a source of individual corroborating examples or as a seed for targeted source follow-up.

## Test B: published community-scale leaf-cut surveys

### Procedure

Searched for the previously proposed Singapore title and for general combinations of:

```text
Megachile leaf cuts plant species survey
leaves cut by bees Megachile supplementary
Megachile leaf fragments plant species nest cells
```

### Result

The exact Singapore title could not be recovered through scholarly search in this environment, and the broader queries returned largely general species pages or nesting biology descriptions rather than accessible datasets with tables/supplements.

### Decision

**Do not adopt meta-analysis yet.** The assumed community-survey data layer has not been demonstrated to be retrievable and extractable across multiple studies.

## Automatic pivot

Both tests fail the primary endpoint:

```text
bee species × plant species × direct material action
```

The next test should not be another unrestricted web search. Test a structured **nest-material evidence** route instead:

```text
published nesting-biology papers
+ trap-nest studies
+ nest-cell dissections
+ explicit identification of leaf/petal fragments
```

This route has a lower candidate volume but is more likely to provide direct material evidence linked to a named bee. It is adopted only if a first fixed batch yields multiple plant-identifiable records with citable primary sources.
