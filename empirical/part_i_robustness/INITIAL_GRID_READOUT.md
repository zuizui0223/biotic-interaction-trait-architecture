# Initial Part I qualitative robustness-grid readout

## Run identity

```text
config:  configs/part_i_robustness_grid.json
runner:  scripts/run_part_i_robustness.py
run id:  initial_qualitative_grid_v1
```

The initial grid contains 162 local phenotype/regime cases:

```text
A = 0.2, 0.5, 0.8
D = 0.2, 0.5, 0.8
R = 0.0, 0.5
P = 0.2, 0.5, 0.8
H = 0.2, 0.5, 0.8
```

Each case is evaluated under four biological parameter scenarios and four
functional-form variants, yielding **2,592 local mixed-partial evaluations**.

## Why two robustness summaries are needed

A different response curve is not the same uncertainty as a different biological
scenario. The run therefore separates:

```text
within scenario:
  does the sign survive changed response curvature?

across scenarios:
  does the sign survive changed interaction tracking,
  pollination obstruction, and shared allocation cost?
```

The first is functional-form robustness. The second is a broad biological
parameter envelope.

## Result 1: functional-form robustness within a fixed scenario

Across the 648 `case × parameter scenario` summaries:

```text
395  structurally_robust across all four functional forms
253  mixed_or_sensitive across functional forms
  0  conditional_majority
```

The result is therefore not an artefact of choosing a linear response everywhere.
For many fixed biological parameter settings, the local sign is preserved when
attraction benefit saturates, defence efficacy saturates, and joint cost curves.

## Result 2: the full biological parameter envelope remains conditional

Across the 162 local cases after combining all four deliberately contrasting
biological scenarios:

```text
  0  structurally_robust across the full envelope
 27  conditional_majority
135  mixed_or_sensitive
```

This is the central first result. The model does **not** support an unconditional
claim that floral attraction and floral barrier traits are generally complementary
or generally substitutable. The sign changes when the biologically decisive
quantities change.

## Scenario-specific signatures

### High antagonism tracking, low pollination obstruction, low shared cost

```text
162 / 162 cases have complementary modal sign
130 / 162 are function-form robust
```

This is the expected complementarity regime: attraction carries antagonism risk,
barrier efficacy suppresses that risk, and the barrier does little damage to
pollination.

### High pollination obstruction and high shared cost

```text
147 / 162 cases have substitutable modal sign
135 / 162 are function-form robust
```

This is the expected substitutability regime: any floral barrier benefit is
overwhelmed by access obstruction and joint allocation penalty.

### Baseline and low-tracking scenarios

Both produce mixed complementary/substitutable regions and many
function-form-sensitive cases. These are the regions that future empirical
parameter envelopes can narrow.

## What this permits in the manuscript

It permits the claim:

> Complementarity is structurally available when floral antagonists track
> attraction and barrier efficacy preserves pollination; substitutability is
> structurally available when barriers obstruct pollination or carry strong
> shared costs. The boundary is conditional and often parameter sensitive.

It does not permit the claim:

> Floral attraction and defence universally trade off, or universally coevolve
> positively.

## Next implementation step

Populate the four-path effect registry. Its role is to constrain the uncertain
channel terms:

```text
A → P  b_A
A → H  d_A
B → H  e_F
B → P  c_D
```

The initial grid deliberately leaves shared allocation cost `c_AD` as a
sensitivity parameter. It will remain so unless an independent allocation/cost
measurement can be justified.