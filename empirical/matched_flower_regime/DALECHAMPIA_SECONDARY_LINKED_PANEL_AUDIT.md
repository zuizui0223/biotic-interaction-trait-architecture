# *Dalechampia scandens* secondary linked-package audit

## Source pair

```text
focal article DOI:  10.1111/j.1600-0706.2013.20780.x
public package DOI: 10.5061/dryad.0k6djh9xx
package title:      Using ecological context to interpret spatiotemporal variation
                    in natural selection
```

The public package is a later data release. Its DataCite metadata lists the
2013 article as `IsCitedBy`; it does **not** declare an allowed
`IsSupplementTo` / `IsDerivedFrom` / `IsPartOf` relationship from the package
to that article. The package therefore cannot be represented as the 2013
article's verified original archived supplement.

## What the public package does establish

The title-independent Dryad audit recovered a 17-file manifest containing 16
population-year tables in `.txt` and `.xlsx` form. Every table header was
recoverable.

Repeated table fields include:

```text
population / year / date / patch / Blossom or ID
upper-bract morphology and area variables
resin or resin-gland variables
pollen / pollenfem / pollenmale / polltotal
seed-predation and total-seed variables where seed outcomes were measured
```

`patch`, `Blossom`, and `ID` recur in multiple population-year panels. This is
strong evidence for a **candidate focal-blossom linkage structure** inside the
later data package, but it remains a header-level conclusion until key semantics
and row joins are documented for the package's own study context.

## Documentation pass

A bounded archive inspection searched only for explicit documentation filenames:
`README`, `metadata`, `methods`, `documentation`, and `stash` variants. Among
all 17 archived members, **none** matched this allow-list.

```text
documentation files recovered: 0
observation-table rows retained: 0
```

Consequently, no in-package variable dictionary or methods note is publicly
recoverable through this archive route. Header names alone cannot establish the
biological role of bract, resin, pollen, or seed fields.

## What it does not establish

```text
not established: the 2013 article's original raw-data provenance
not established: the later package's study methods or variable dictionary
not established: a separately measured floral B_flower resistance trait
not established: a direct four-path effect estimate
not established: D1, D2, or D3 status
```

Seed predation is an antagonist outcome; it cannot be used as a floral barrier
trait. Bract area, resin variables, and floral geometry must be classified from
primary-source methods before any role assignment. In particular, reward-use or
pollen-transfer traits must not be relabelled as `B_flower` by default.

## Current disposition

```text
M0_high_information_secondary_linked_package
```

Retain the package as a source lead. Do not enter its variables into the
four-path registry or use them to support the 2013 Oikos article until a source
relationship and trait-function screen are completed.
