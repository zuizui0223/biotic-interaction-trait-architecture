# Predeclared pollinator-image annotation protocol: *Gymnadenia rhellicani*

## Purpose

This protocol defines the only route by which the Figshare camera archives may
become an individual or experimental-unit `A_to_pollination` outcome. It is
written before opening or counting image frames.

The focal floral trait is colour morph. Colour is treated as an attraction-signal
candidate only for this extraction because the article tests pollinator colour
preferences. This role assignment does not establish an effect.

## Separate designs

The two camera datasets are separate experiments and must never be pooled at
frame, visit, or effect-estimate level.

```text
2016 design: in-situ black/red flower-pair comparison
2017 design: cut-inflorescence triplet comparison across black/red/white
```

Each design receives its own manifest audit, exposure accounting, annotation
file, and effect estimate, if eligible.

## Annotation unit

```text
primary unit:      one camera frame
secondary unit:    one morph-specific floral display within a frame
visitor event:     one insect visibly contacting or landing on the target display
```

A moving insect that cannot be linked to a target display is recorded as
`unassigned` and excluded from morph-specific counts. A single insect visible on
multiple adjacent frames is not deduplicated across frames unless frame timing
and image sequence permit a predeclared continuous-track rule; otherwise the
outcome is framed as occupied-frame rate, not unique-visitor count.

## Required fields before any biological model

For every eligible frame/morph display, record only these annotation fields:

```text
experiment_year
camera_archive
camera_or_sequence_id
frame_timestamp_or_order
morph
frame_usable (yes/no)
exposure_interval_seconds
bee_landing (0/1)
fly_landing (0/1)
other_landing (0/1)
unassigned_insect (0/1)
annotation_reason_if_unusable
```

No fruit, seed, fitness, or herbivory field is joined at this stage.

## Exposure and exclusion rules

- A frame is unusable only for a predeclared technical reason: missing target,
  obscured target, camera failure, or unreadable morph identity.
- Exclusion reason is mandatory; no manual quality exclusion is permitted.
- Exposure is the known elapsed interval represented by the frame. If interval
  cannot be recovered from archive metadata or article methods, the dataset may
  support frame occupancy only, not a time-standardised visit rate.
- The number of displays visible for each morph must be recorded. A morph-level
  count without display exposure cannot be interpreted as preference.

## Coder reliability gate

Before full annotation, a random, reproducible 10% sample of usable frames from
each year-design is independently annotated twice. The protocol proceeds only
if morph identity and bee/fly/other landing classification have documented
agreement. Disagreements are resolved by a written decision rule added to this
protocol before the remainder is coded.

## Eligible estimand

A model may be predeclared only after manifest and annotation audits establish:

```text
- morph-specific target-display exposure;
- recoverable frame exposure or fixed frame interval;
- no unresolved camera/morph mapping ambiguity; and
- enough independent camera or temporal blocks for a design-aware model.
```

The default candidate outcome is an occupied-frame or landing-event rate per
morph-specific display exposure, analyzed separately by 2016 and 2017 design.
No individual fruit-set or seed-set value is used as a substitute for visitor
counts.

## Interpretation boundary

An image-derived colour-morph effect is a design-specific association or
experiment result. It does not establish a universal colour effect, a floral
barrier trait, a shared A×B allocation cost, or D1/D2/D3 evidence unless the
remaining required paths and common units are independently demonstrated.
