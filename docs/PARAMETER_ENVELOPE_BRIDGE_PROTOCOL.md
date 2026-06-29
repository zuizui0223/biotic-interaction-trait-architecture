# Parameter-envelope bridge protocol

## Why a separate bridge is required

The four-path synthesis estimates published effects on their reported scales:

```text
A → P  standardized slope, log response ratio, odds ratio, etc.
A → H  standardized slope, log response ratio, odds ratio, etc.
B → H  standardized slope, log response ratio, odds ratio, etc.
B → P  standardized slope, log response ratio, odds ratio, etc.
```

The Part I model uses dimensionless response parameters:

```text
b_A  attraction_gain
 d_A attraction_tracking
 e_F floral_defence_efficacy
 c_D defence_pollinator_cost
```

Those quantities are not interchangeable by default. A standardized regression
slope is not silently a dimensionless fitness-model coefficient; a visitor rate
is not automatically a pollen-transfer effect; and `e_F` must remain bounded in
`[0, 1]` under the present score.

## Contract rule

A parameter envelope may enter the empirical robustness run only after a
machine-readable calibration contract declares all of:

```text
1. source effect-role, scale, and causal-status stratum;
2. target Part I parameter;
3. the selected synthesis summary or source studies;
4. why the reported outcome is a valid proxy for that channel;
5. a predeclared dimensionless low/mid/high envelope;
6. any truncation or bound used by the model;
7. whether the values are data-calibrated, scenario-based, or unresolved.
```

The code accepts an explicit low/mid/high envelope. It does not manufacture one
from a coefficient through an undisclosed conversion.

## Allowed calibration states

```text
awaiting_synthesis
  no compatible scale-specific effect summary yet

manual_calibration_required
  a compatible summary exists, but proxy mapping or units still need a written decision

calibrated_envelope
  source, proxy, and low/mid/high dimensionless values are declared

not_parameterizable
  evidence remains useful descriptively but cannot map to the current parameter
```

Only `calibrated_envelope` may generate empirical Part I scenarios.

## Required target mapping

| Part I parameter | Required effect role | Typical valid outcome |
|---|---|---|
| `attraction_gain` (`b_A`) | `A_to_pollination` | pollen transfer/effectiveness or a declared visitation-to-service proxy |
| `attraction_tracking` (`d_A`) | `A_to_antagonism` | flower-stage damage, florivory, seed predation, robbery, or pollen theft with denominator |
| `floral_defence_efficacy` (`e_F`) | `B_to_antagonism` | documented reduction in a flower-stage antagonist outcome |
| `defence_pollinator_cost` (`c_D`) | `B_to_pollination` | documented pollination/access reduction caused by the barrier trait |

`attraction_defence_shared_cost` (`c_AD`) is **not** filled by this bridge. It
remains a scenario parameter unless independent allocation/cost evidence is
available.

## Empirical-envelope run

Once all four channel contracts are calibrated, the bridge produces low/mid/high
scenario values. The empirical envelope sweep then varies those declared values
inside the functional-form robustness framework.

```text
scale-specific effect summary
→ written calibration contract
→ dimensionless low/mid/high parameter envelope
→ empirical-envelope robustness sweep
```

The final results must still report both the generic qualitative grid and the
calibrated empirical envelope. Neither replaces the other.