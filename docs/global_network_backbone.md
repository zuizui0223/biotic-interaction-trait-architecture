# Global network backbone for validating trait-architecture simulations

## Role in the program

The regime-map simulation supplies conditional predictions; it does not establish that any empirical regime occurs. The global-network backbone supplies a test of partial observational signatures.

| Simulation component | Observational signature | Required data |
|---|---|---|
| Attraction module \(A\) | plant mutualist degree, weighted visitation, pollinator guild breadth | pollination edges plus floral trait module |
| Defence module \(D\) | antagonist degree, herbivore/florivore link structure, damage where available | plant-antagonist edges plus defence proxy module |
| Regime-dependent \(\operatorname{Cov}(A,D)\) | changes in within-network attraction--defence association with mutualist/antagonist context | comparable network metadata and separate interaction layers |
| Reproductive assurance \(R\) | pollinator uncertainty associated with selfing/delayed-selfing traits | a dedicated flowering-plant case study, initially Campanula rather than broad network data |

No single network archive is assumed to contain all four components.

## Analysis sequence

1. Normalise every source into the interaction and metadata contracts in `empirical/global_networks/DATA_CONTRACT.md`.
2. Run `examples/audit_network_backbone.py` before trait joins or graph metrics.
3. Freeze a source-specific registry with downloads, checksums, source versions, taxonomic reconciliation, and exclusions.
4. Analyse pollination and antagonism separately; do not create a composite interaction pressure until a predeclared scale and transformation are justified.
5. Fit within-network models before cross-network pooling.
6. Use leave-one-network-out sensitivity and phylogenetic sensitivity before interpreting a trait association.
7. Treat positive/negative \(A\)--\(D\) associations as conditional signatures, not evidence that a named defence mechanism caused them.

## Initial source audit

The initial audit found that Web of Life visibly exposes both pollination and plant-herbivore categories and provides data-download controls. However, the live download generation returned an error in the browser test, so it cannot yet be treated as an automated dependency. citeturn338016view1turn598902view0turn598902view1

The next source test must compare:

- a bulk archive or reproducible snapshot of pollination networks;
- a plant-herbivore / florivore collection with network and locality IDs;
- trait coverage after accepted-name reconciliation.

The source with the strongest contract, not the largest nominal edge count, becomes the backbone.
