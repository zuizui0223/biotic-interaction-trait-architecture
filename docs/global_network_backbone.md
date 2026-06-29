# Global network backbone for testing trait-architecture simulations

## Role in the program

The regime-map simulation supplies conditional predictions; it does not establish that any empirical regime occurs. The empirical layer can only test **partial observational signatures**, and it must use data sources that are reproducibly obtainable without manual, one-off trait requests.

| Simulation component | Observational signature | Required data |
|---|---|---|
| Floral attraction module \(A_{flower}\) | plant mutualist degree, weighted visitation, pollinator guild breadth | pollination edges plus non-circular floral traits measured in the same study/network context |
| Floral barrier module \(B_{flower}\) | florivore/seed-predator link structure, damage where available | flower/capitulum traits plus antagonist observations from the same study context |
| Leaf-quality module \(Q_{leaf}\) | leaf-herbivore degree, host breadth, or interaction structure | plant-antagonist networks plus source-resolved, directly observed leaf traits |
| Leaf-resistance module \(B_{leaf}\) | leaf-herbivore link structure or damage | herbivory networks plus compatible mechanical/chemical resistance traits |
| Regime-dependent covariance | within-network trait associations conditional on mutualist/antagonist context | matched dual-layer studies; never unmatched global databases |

No single archive is assumed to contain all components.

## Source-contract results

### Web of Life: retained only as a pollination edge source

The live Web of Life endpoints passed the source-contract and taxonomic-orientation probes:

- network metadata and weighted edge records can be retrieved programmatically;
- pollination is a large layer whereas plant-herbivore coverage is too small for the defence backbone;
- plant versus animal side can be recovered for the overwhelming majority of pollination networks by bounded GBIF taxonomic checks.

Web of Life is therefore a candidate **pollination-edge** source. It is neither an all-guild backbone nor a trait source.

### BIEN: floral trait backbone rejected; leaf trait source remains a feasibility candidate

BIEN was reachable programmatically, but the direct-record screen for two non-circular floral candidates on a deterministic sample of 30 oriented Web of Life pollination networks was poor:

| Trait | Taxa with direct record | Screen coverage |
|---|---:|---:|
| flower color | 4 / 30 | 13.3% |
| inflorescence length | 2 / 30 | 6.7% |

BIEN is therefore rejected as an automated **floral** trait backbone.

This result does not establish whether BIEN can support automatic retrieval of
leaf-economics traits. That is a separate, source-specific feasibility test and
must use direct records for `SLA/LMA`, `LDMC`, leaf N, leaf P, and leaf thickness.
Passing that test would establish only trait-source availability; it would not
turn Web of Life pollination networks into an herbivory analysis.

### TRY: not an active dependency

TRY can supply custom records, but a registered, manually managed data request is
not a viable dependency for this program. The TRY manifest and receipt utilities
are retained as optional infrastructure only; no current result, milestone, or
analysis path waits for a TRY request or download.

## Public-data-first decision sequence

The next empirical task is a **two-gate feasibility test**, using only sources
that can be retrieved reproducibly by code:

1. **Trait gate:** test whether a public, script-accessible source yields enough
   *direct* records for each leaf candidate trait on a declared plant set.
2. **Network gate:** test whether a public plant-antagonist source yields enough
   independently sampled, metadata-complete herbivory networks for the same
   plant set and analysis scale.

Only when both gates pass do we run a global leaf-quality/leaf-herbivory model.
If either fails, we do not manually fill the gaps or use imputed data as a
substitute; we record the global route as not currently identified and pivot to
matched-study evidence synthesis.

## What is feasible now

```text
Theory + simulation
    → complete independently of any trait database.

Automated leaf feasibility screen
    → public leaf-trait provider × a declared network plant set.

Automated herbivory-network feasibility screen
    → public interaction provider × metadata and sampling contract.

Matched-study floral synthesis
    → only studies where floral traits and pollination edges were measured in
      the same study/network context.
```

The floral route is not a 3,000-species trait join. It is a study-level synthesis
or a future targeted case, because no retained public source currently provides
adequate, directly measured floral traits across the Web of Life plant set.

## Analysis sequence after a route passes

1. Freeze a source-specific registry with downloads, checksums, source versions,
   taxonomic reconciliation, and exclusions.
2. Normalise interactions and metadata into the network contract.
3. Audit direct trait coverage per trait; do not count imputed values as primary
   records.
4. Fit within-network models before cross-network pooling.
5. Use leave-one-network-out and phylogenetic sensitivity before interpreting an
   association.
6. Treat positive/negative trait associations as conditional signatures, not
   evidence that a named mechanism caused them.
