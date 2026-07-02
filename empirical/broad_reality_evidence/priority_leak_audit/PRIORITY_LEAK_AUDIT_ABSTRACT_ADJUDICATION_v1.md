# Priority-leak audit: abstract-level adjudication v1

## Purpose

This audit tests a narrow operational question:

> Does the metadata priority screen lose direct target-route studies relative to biologically contextual non-priority candidates?

It does not revise the retrieval queries, route definitions, priority rule, inclusion rule, hypothesis, or broad direction registry.

## Frozen source receipt

```text
Crossref harvest workflow:      28563489357
Workflow artifact:              8028390020
Artifact digest:                sha256:ce29ec7e7ce1d537e2bf2e1b953ef17cf87e030e6cc9b61f703e222e51c69a7f
Audit queue:                    300 rows
Sampling design:                5 route families × 2 audit groups × 30 rows
Crossref deposited abstracts:   137 rows
No deposited abstract:          163 rows
```

The queue and its packet are deterministic audit inputs. The source packet remains the retrieval receipt; this document reports a separate abstract-resolution decision layer.

## Coding rule

Every deposited abstract was reviewed using the existing broad codebook. The materializer therefore starts such rows as:

```text
source_screen_status = included_for_source_coding
source_access_status = abstract_only
route_screen_status = direct_route_absent
```

That default means only that the **target audit route** was not directly assessed in the available abstract. It does not mean that the study is biologically irrelevant, that no other route exists, or that the relationship is absent in full text.

Twenty explicit overrides are registered in `priority_leak_audit_abstract_overrides_v1.csv`:

```text
11  direct target-route records
8   non-primary/nonbiological exclusions
1   commentary-pointer metadata record retained as unassessed
```

All 163 rows without a deposited abstract, plus the commentary-pointer row, remain `unassessed` rather than being counted as route absence.

## Audit outcome

```text
source-screen status
  included_for_source_coding: 128
  excluded:                     8
  unassessed:                 164

route-screen status
  direct_route_present:        11
  direct_route_absent:        125
  unassessed:                 164
```

| Route | Group | Screenable | Direct target-route present | Yield |
|---|---|---:|---:|---:|
| A_to_pollination | priority | 20 | 6 | 0.3000 |
| A_to_pollination | biological_nonpriority | 9 | 1 | 0.1111 |
| A_to_antagonism | priority | 17 | 1 | 0.0588 |
| A_to_antagonism | biological_nonpriority | 6 | 0 | 0.0000 |
| B_to_antagonism | priority | 19 | 1 | 0.0526 |
| B_to_antagonism | biological_nonpriority | 4 | 0 | 0.0000 |
| B_to_pollination | priority | 20 | 0 | 0.0000 |
| B_to_pollination | biological_nonpriority | 9 | 0 | 0.0000 |
| joint_channels | priority | 18 | 1 | 0.0556 |
| joint_channels | biological_nonpriority | 14 | 1 | 0.0714 |

## Direct target-route records retained at abstract resolution

| Route | Group | DOI | System / abstract-level basis |
|---|---|---|---|
| A_to_pollination | priority | `10.1093/botlinnean/boae061` | Floral colour and scent contrasted with visitation and pollinator-exclusion fruit-set outcomes. |
| A_to_pollination | priority | `10.1111/njb.02308` | Floral display size assessed against visitation and fruit set. |
| A_to_pollination | priority | `10.1111/j.0030-1299.2006.14289.x` | Flower colour morph compared with specialist-bee foraging. |
| A_to_pollination | priority | `10.1111/1365-2745.13348` | Floral abundance and colour similarity related to pollen receipt and pollen-tube fitness. |
| A_to_pollination | priority | `10.1002/ece3.73221` | Floral orientation experimentally reoriented with visitation and pollination efficiency measured. |
| A_to_pollination | priority | `10.1111/plb.13587` | Resupination manipulated with pollen removal/deposition measured. |
| A_to_pollination | biological_nonpriority | `10.1111/nph.16482` | Floral orientation experimentally altered with pollination accuracy measured. |
| A_to_antagonism | priority | `10.3732/ajb.89.8.1270` | Flower morphology and exserted-organ position compared with floral-herbivore damage. |
| B_to_antagonism | priority | `10.1111/1365-2435.13332` | Floral benzyl-acetone emission removed with florivore colonization and floral damage measured. |
| joint_channels | priority | `10.1007/s11829-026-10238-5` | Ant treatment with legitimate visitation, nectar theft, herbivores, and reproduction jointly assessed. |
| joint_channels | biological_nonpriority | `10.1111/j.1365-2699.1996.tb00005.x` | Fig-wasp pollination intensity and seed destruction jointly described. |

## Interpretation

For the assessed abstract subset, the priority group had higher direct-route yield for `A_to_pollination`, `A_to_antagonism`, and `B_to_antagonism`. The joint-channel yields are nearly identical but are based on one retained record per group. `B_to_pollination` had zero retained direct records in either group.

The appropriate conclusion is therefore limited:

> The existing priority screen is a defensible first reading queue for the assessed abstract subset. This audit did not reveal a large leakage of direct A-to-P, A-to-H, or B-to-H studies into the biological non-priority group. It does not show that the screen is complete, and the zero B-to-P result is a gap in this audit sample, not evidence that B-to-P studies do not exist.

The 163 rows without a deposited abstract and the one unusable metadata record remain unresolved. They should be revisited only through a source-access expansion or a targeted full-text pass, not reclassified from title words.

## Boundaries

- This is a priority-screen audit, not an effect-size synthesis.
- `direct_route_absent` means the target route was not recoverable from the available abstract, not that a biological relationship is absent.
- No route record from this audit is automatically added to `broad_route_records.csv`.
- No direction, causal claim, or quantitative eligibility is inferred here.
- The broad direction registry remains its own frozen, source-adjudicated evidence slice.
