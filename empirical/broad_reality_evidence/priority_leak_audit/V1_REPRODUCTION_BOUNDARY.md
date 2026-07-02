# V1 reproduction boundary

The abstract-level priority-leak audit v1 is tied to one fixed source receipt:

```text
workflow: 28563489357
artifact: 8028390020
digest:   sha256:ce29ec7e7ce1d537e2bf2e1b953ef17cf87e030e6cc9b61f703e222e51c69a7f
```

The decision overlay is intentionally keyed by audit group, target route, rank, candidate ID, and DOI. It can be applied only to that matching frozen packet.

A fresh Crossref harvest can alter both ranking and the sampled top-30 candidates. A new live packet is therefore a new, unassessed audit cohort. The routine harvest workflow retains that current packet and builds a blank coding sheet; it does not overwrite or revalidate v1 against live retrieval output.

Do not relax the rank check merely to make a live reharvest fit the v1 overlay. That would merge different audit samples and invalidate the registered comparison.
