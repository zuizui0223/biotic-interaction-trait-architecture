# Evidence atlas v0: what is identified, blocked, and next

## Purpose

This atlas is the decision layer between the effect registry and future
literature or field work. It prevents a large list of candidates from being
mistaken for a broad empirical synthesis.

Read `EVIDENCE_STATUS_v0.csv` together with the effect registry:

```text
registry = verified study × trait × outcome × model effects
atlas    = verified effects plus high-information, blocked, and inaccessible cases
```

The atlas is not a meta-analysis, an evidence-weighted parameter envelope, or a
claim about a universal attraction–barrier trade-off.

## Verified effect coverage

| Part I path | Independent study clusters | Compatible effect-scale strata | Current state |
|---|---:|---|---|
| `A_to_pollination` | 1 | standardized slope: 1 | one observational Impatiens cluster |
| `A_to_antagonism` | 2 | standardized slope: 1; log odds ratio: 1 | two clusters, not poolable |
| `B_to_antagonism` | 1 | standardized slope: 1 | one observational Impatiens cluster |
| `B_to_pollination` | 1 | standardized slope: 1 | one observational Impatiens cluster |

There are five registered effects from two independent study clusters. All are
observational. No role × scale × causal-status stratum has two compatible,
independent studies.

## Evidence-state classes

```text
verified_effect_panel
    Effect records pass source, unit, denominator, model, and uncertainty gates.

verified_one_path_effect
    One path is registered; remaining paths are explicitly absent or ineligible.

reported_table_screen_pending
    Public full text is the one remaining source route; screen it once using a
    predeclared trait, denominator, uncertainty, and independence contract.

verified_source_unidentified_visit_effect
    Source is verified but the response cannot be estimated because exposure or
    unit mapping is unresolved.

high_information_not_eligible / aligned_mechanism_blocked / M1_descriptive_not_quantitative
    Useful biological context, but not eligible for a registry effect.

secondary_package_not_promoted
    A later or unverified package exists, but article relation, methods, or trait
    semantics are insufficient for effect extraction.

public_source_inaccessible
    The public-only source route is closed; this is an access result, not a
    biological null result.
```

## Immediate work rule

There is **one** remaining literature action before broad discovery resumes:

```text
Gorden and Adler (2016), Impatiens capensis
DOI: 10.1002/ecs2.1326
```

Conduct one public full-text/table screen that answers only:

1. Is anthocyanin or condensed tannin measured as a flower-specific trait?
2. Is a floral-antagonist outcome defined with a denominator or exposure?
3. Is a direct trait-to-antagonist estimate with uncertainty reported or
   reproducible from a declared aggregate table?
4. Does its observation panel overlap the 2018 Impatiens panel?

If any answer needed for eligibility is no or unrecoverable, record the reason
and close the source. Do not create a new extraction pipeline for it.

## Stopping rules for public-literature work

### Stop broad candidate discovery now

Do not add more broad OpenAlex queries or enlarge the fixed candidate universe
until the pending 2016 Impatiens table screen is closed.

### Stop role-specific synthesis before pooling

Do not calculate a pooled mean, empirical parameter envelope, or "typical"
direction for a path until a role × reported-scale × causal-status stratum has
at least two independent study clusters. Multiple papers using the same field
panel are one cluster, not replication.

### Stop image-derived pollination extraction without exposure mapping

Do not count or model *Gymnadenia rhellicani* frames until a public source links
camera/sequence identifiers to displayed morph(es), display number, and frame
interval or total observation duration. Fruit, seed, and fitness outcomes cannot
replace this mapping.

### Stop D2/D3 claims

Do not describe the program as D2 or D3 until there is a linked reproductive
fitness surface and, for D3, an independently measured/calibrated A×B allocation
or shared-cost component.

## Transition trigger: public synthesis to a self-contained field panel

The public route has achieved a feasibility result: a rigorous four-path ledger
is possible, but compatible independent replication is sparse. Move the main
scientific effort to a self-contained field panel when either condition holds:

```text
A. the one pending Gorden and Adler (2016) screen closes without an eligible,
   independent B_to_antagonism estimate; or
B. no second compatible independent effect is added to any sparse path after
   one targeted full-text/table screen per verified public-source route.
```

A self-contained pilot should measure on the same biological unit:

```text
A_flower: visual/display trait such as colour, size, orientation, or guide
B_flower: independently justified flower-specific access/resistance trait
P:        visitor contact, pollen transfer, or another declared pollination proxy
H:        floral antagonism with exposure/denominator
W:        fruit/seed/viable offspring response
```

The pilot should be framed as a D1 design target, not as proof that every
measured floral physical or chemical trait is defence.

## Interpretation boundary

The current atlas supports a conditional, trait- and context-specific research
program. It does not support a universal sign for attraction–antagonism links,
a pooled empirical regime map, or a causal allocation trade-off.