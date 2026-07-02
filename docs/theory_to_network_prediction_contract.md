# Theory-to-network prediction contract

## Active scope

The active program has three linked layers:

```text
1. derive qualitative conclusions and sensitivity boundaries from the
   attraction--defence regime model;
2. map broad L1/L2 literature coverage for the empirical channels entering that model;
3. test predeclared observational signatures with matched global network and trait data where available.
```

Campanula, Cirsium, and Megachile remain possible future mechanistic cases. They
are not required to establish this first theory-plus-global-data program.

The broad literature layer is a coverage and sign/context interface. It does not
replace the source-resolved network layer and does not calibrate model coefficients.

## Exact result for the current score

For the fitness score implemented in `trait_architecture.model`, the exact local
mixed partial with respect to attraction `A` and defence `D` is

\[
\frac{\partial^2 W}{\partial A\,\partial D}
=
H\,d_A\,e_F
-
P\,b_A\,c_D\,e^{-c_DD}(1-c_RR)
-
c_{AD}.
\]

where:

- `P` is pollinator service;
- `H` is floral-antagonist pressure;
- `d_A` is antagonist tracking of attractive display;
- `e_F` is floral-defence efficacy;
- `b_A` is attraction-mediated outcross gain;
- `c_D` is defence obstruction of pollinator access;
- `c_R` is assurance-related outcross dilution; and
- `c_AD` is a shared attraction--defence investment cost.

The implementation in `trait_architecture.ad_interaction_condition` evaluates
this expression exactly and is regression-tested against finite differences of
the score.

### Interpretation

| Local score relation | Exact condition | Meaning inside this model |
|---|---|---|
| complementarity | `H*d_A*e_F > P*b_A*c_D*exp(-c_D*D)*(1-c_R*R) + c_AD` | Increasing defence raises the marginal score of attraction, and vice versa. |
| substitutability | left side is smaller | Increasing defence lowers the marginal score of attraction, and vice versa. |
| neutral local curvature | equality | The score contains no direct local A--D complementarity or substitution at that point. |

This is **not** a theorem that a natural population must show a positive or
negative trait covariance. It is an exact result only for the declared model
score and state. The sign of covariance among simulated regime optima is a
separate, grid-dependent simulation summary. The sign observed among species or
populations is a separate, data-generating-process-dependent statistic.

### Immediate model consequences

1. A negative A--D relation is not a default: it requires pollinator-access
   obstruction and/or shared investment cost to exceed floral-damage relief.
2. A positive A--D relation is possible when attractive displays increase floral
   antagonism and defence selectively suppresses the associated damage without
   strongly blocking pollination.
3. Leaf-consumer pressure `L` does not occur directly in the local A--D mixed
   partial. It can raise optimal defence, but it changes A--D association only
   indirectly through shared costs, architectural coupling, or the distribution
   of regimes.
4. If floral antagonists do not track display or floral defence is ineffective,
   no finite floral-antagonist pressure can by itself create local A--D
   complementarity in this model.

## What the broad L1/L2 literature layer can test

The broad corpus is a query-derived discovery map. After fixed-candidate abstract
retrieval, it can identify shallow **candidate coverage** for organ-matched
channels:

```text
A_flower + P language  -> A_to_pollination candidate coverage -> b_A status
A_flower + H language  -> A_to_antagonism candidate coverage -> d_A status
B_flower + H language  -> B_to_antagonism candidate coverage -> e_F status
B_flower + P language  -> B_to_pollination candidate coverage -> c_D status
```

The source-adjudicated direction registry then labels each term as directionally
anchored, condition-dependent, or not identified. The combined output does not
produce a numerical value for `b_A`, `d_A`, `e_F`, `c_D`, `c_AD`, `P`, `H`, or
`c_R`.

`c_AD` requires matched attraction/defence allocation observations. `c_R*R`
requires a reproductive-assurance/outcross-dilution observation model. Neither is
identified by the active L1/L2 map, and both remain explicit sensitivity axes.

## What the global-network layer can test

Global data cannot observe `P`, `H`, or the score components directly. It can
only test **predeclared observational signatures** after a source-specific
observation model is written.

### Attraction--mutualist module

**Unit:** a plant within a single pollination network.

**Candidate response/context variables:** standardised weighted interaction
strength, degree, partner-guild breadth, and network role. Raw interaction
counts from networks with different effort must not be pooled as though they
were comparable.

**Trait module:** direct floral measurements or record-level floral traits,
including flower size, display/inflorescence traits, colour, reward, floral
orientation, and flowering duration where a source provides them. `Pollination
syndrome` is excluded because it encodes the interaction domain being explained.

**Permitted claim:** an attraction-trait module is conditionally associated with
pollination-network structure after the declared sampling, taxonomy, and
phylogenetic controls.

### Defence--antagonist module

**Unit:** a plant within a single antagonist network.

**Interaction layers:** herbivory, florivory, seed predation, plant--ant, and
wood/stem-borer interactions are separate by default. They must not be silently
combined into a generic antagonist-pressure index.

**Trait module:** match defence traits to the attacked organ. For example,
leaf toughness, LDMC, thickness, and pubescence belong to leaf-consumer tests;
floral or inflorescence barriers belong to florivory tests; wood density,
bark/wood chemistry, and stem architecture belong to wood-borer tests such as
Cerambycidae. A cross-organ defence score requires a separately declared
biological bridge.

**Permitted claim:** an organ-matched defence-trait module is conditionally
associated with antagonist-network structure.

### Joint A--D test

A direct test of the A--D prediction requires a **matched unit** carrying:

1. attraction traits and defence traits;
2. pollination and antagonist information for the same site/time/network context
   or an explicitly justified alignment;
3. an organ-matched antagonist layer; and
4. a predeclared phylogenetic and sampling model.

Separate global pollination and herbivory databases can support the two module
analyses above. They cannot, on their own, establish a joint regime-dependent
A--D covariance.

## Predeclared analysis sequence

1. Run the model's parameter sweep and report both stable and mixed sign regions.
2. Build the fixed-corpus broad abstract map and its theory-term evidence status.
3. Freeze a source registry and normalise edge and metadata tables under
   `empirical/global_networks/DATA_CONTRACT.md`.
4. Audit network count, geographic coverage, trait coverage, interaction-type
   integrity, provenance, and weights before graph metrics are calculated.
5. Test attraction--mutualist and defence--antagonist modules separately within
   networks before any cross-network pooling.
6. Use leave-one-network-out, trait-source, taxonomic-reconciliation, and
   phylogenetic sensitivity analyses.
7. Attempt the joint A--D test only if an explicitly matched dual-layer dataset
   passes the data contract.

## Falsification and non-identifiability rules

- A failed source-coverage audit is a data limitation, not negative evidence for
  the model.
- A model sign that changes across declared parameter scenarios is a valid
  `mixed` result, not a reason to choose the attractive sign post hoc.
- An observed trait association that conflicts with a model scenario rules out
  that scenario only after the observation model and proxy mapping are declared.
- No matched dual-layer data means the joint A--D prediction is **not tested**;
  it must not be relabelled as zero support or as an empirical trade-off.
