# Theory and simulation specification

## Objective

Map interaction regimes to qualitative trait architectures without pretending that the first model is an empirically calibrated evolutionary prediction.

## Minimal modules

```text
attraction A
  floral display, nectar guide, flower size, nectar, orientation

defence/access D
  leaf toughness, LDMC, thickness, spines, sticky secretion,
  chemical deterrence, physical access barriers

reproductive assurance R
  autonomous selfing, delayed selfing, herkogamy, dichogamy,
  floral longevity
```

## Interaction regimes

```text
P: pollinator service
H: floral herbivore / florivore pressure
L: leaf-cutter / leaf-consumer pressure
```

The initial simulator will sweep a low-dimensional parameter grid and classify strategies rather than simulate whole plant genomes.

## Strategy classes to detect

```text
attraction withdrawal: A low, D variable, R high
dual insurance:        A high, D variable, R high
guarded attraction:    A high, D high, R high
open attraction:       A high, D low,  R low/moderate
defence-first:         A low,  D high, R variable
```

## First falsifiable predictions

1. Attraction and defence covary negatively only when defence directly reduces pollinator access or shares a binding allocation budget with attraction.
2. Attraction and defence covary positively when antagonists track attractive displays and defence selectively reduces antagonist cost.
3. Pollinator decline does not uniquely imply attraction loss; the response depends on assurance efficiency and the outcrossing benefit retained by attraction.
4. Leaf-cutter pressure affects leaf-related defence/access traits directly, but can indirectly alter floral strategy only through shared costs, shared architecture, or correlated trait modules.

## Link to empirical chapters

The Megachile chapter tests the leaf-resource side first. Campanula and Cirsium chapters test floral attraction, assurance, and floral defence. Empirical data may falsify a regime prediction, but do not retroactively validate the entire model class.
