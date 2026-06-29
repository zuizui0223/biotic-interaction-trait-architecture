# Global network backbone for validating trait-architecture simulations

## Role in the program

The regime-map simulation supplies conditional predictions; it does not establish that any empirical regime occurs. The global-network backbone supplies tests of partial observational signatures.

| Simulation component | Observational signature | Required data |
|---|---|---|
| Attraction module \(A\) | plant mutualist degree, weighted visitation, pollinator guild breadth | pollination edges plus a non-circular floral-trait module |
| Defence module \(D\) | antagonist degree, herbivore/florivore link structure, damage where available | plant-antagonist edges plus a defence-proxy module |
| Regime-dependent \(\operatorname{Cov}(A,D)\) | changes in within-network attraction--defence association with mutualist/antagonist context | comparable network metadata and separate interaction layers |
| Reproductive assurance \(R\) | pollinator uncertainty associated with selfing/delayed-selfing traits | a dedicated flowering-plant case study, initially Campanula rather than broad network data |

No single archive is assumed to contain all four components.

## Source-contract results

### Web of Life: retained for the pollination edge layer

The live Web of Life endpoints passed the source-contract and taxonomic-orientation probes:

- network metadata and weighted edge records can be retrieved programmatically;
- pollination is a large layer whereas plant-herbivore coverage is too small for the defence backbone;
- plant versus animal side can be recovered for the overwhelming majority of pollination networks by bounded GBIF taxonomic checks.

Web of Life is therefore retained **only** as the candidate pollination-edge layer. It is not the all-guild backbone and it is not by itself a trait source.

### BIEN: rejected as the automated floral-trait backbone

The live BIEN trait catalog exposes five floral-keyword candidates: `flower color`, `flower pollination syndrome`, `inflorescence length`, `plant flowering begin`, and `plant flowering duration`.

`flower pollination syndrome` is excluded because it encodes the interaction domain to be explained. The two non-circular attraction candidates tested in a deterministic sample of 30 oriented Web of Life pollination networks had low direct-record coverage:

| Trait | Taxa with direct record | Screen coverage |
|---|---:|---:|
| flower color | 4 / 30 | 13.3% |
| inflorescence length | 2 / 30 | 6.7% |

The BIEN API itself was reachable, so this is a coverage failure rather than a technical-access failure. BIEN is retained for optional taxonomic reconciliation and structural covariates, but rejected as the main attraction-trait provider.

## Recommended backbone now

```text
Web of Life pollination edges
  +
TRY custom trait export for the oriented Web of Life plant set
  +
Campanula for the reproductive-assurance causal case
  +
a separate antagonist source for the defence module
```

TRY is the appropriate next provider because it supplies customized trait records for selected species and traits. Its Data Explorer exposes content information, whereas actual values are delivered through a registered data request. The request must exclude `pollination syndrome` from predictive trait modules and preserve record-level provenance.

`prepare-try-wol-request.yml` generates a deterministic species manifest from the oriented Web of Life plant side. The artifact is the input to the TRY request, not empirical data itself.

## Analysis sequence

1. Normalise each source into the interaction and metadata contracts in `empirical/global_networks/DATA_CONTRACT.md`.
2. Run source-contract tests before trait joins or graph metrics.
3. Freeze a source-specific registry with downloads, checksums, source versions, taxonomic reconciliation, and exclusions.
4. Analyse pollination and antagonism separately; do not create a composite interaction pressure until a predeclared scale and transformation are justified.
5. Fit within-network models before cross-network pooling.
6. Use leave-one-network-out sensitivity and phylogenetic sensitivity before interpreting a trait association.
7. Treat positive/negative \(A\)--\(D\) associations as conditional signatures, not evidence that a named defence mechanism caused them.