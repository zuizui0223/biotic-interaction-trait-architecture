# Host-evidence collection pipeline

## What this pipeline does

```text
curated bee checklist
  -> bilingual reproducible queries
  -> candidate bibliographic metadata
  -> deterministic duplicate audit
  -> source-specific review packets
  -> LLM-assisted candidate extraction
  -> human evidence grading and taxonomy reconciliation
  -> validation
  -> primary host plant universe
```

The LLM step is optional and deliberately cannot write directly into the primary host universe.

## Pilot workflow

Start with a curated checklist of three Japanese *Megachile* taxa in `data_raw/megachile_species.csv`, copied from `megachile_species_template.csv`.

```bash
python empirical/megachile_leaf_resource/scripts/01_build_queries.py \
  --species empirical/megachile_leaf_resource/data_raw/megachile_species.csv \
  --output empirical/megachile_leaf_resource/data_raw/search_queries.csv

python empirical/megachile_leaf_resource/scripts/02_collect_metadata.py \
  --queries empirical/megachile_leaf_resource/data_raw/search_queries.csv \
  --provider crossref \
  --mailto your-email@example.org \
  --output empirical/megachile_leaf_resource/data_raw/source_metadata_raw.csv \
  --raw-dir empirical/megachile_leaf_resource/data_raw/metadata_responses

python empirical/megachile_leaf_resource/scripts/03_deduplicate_sources.py \
  --input empirical/megachile_leaf_resource/data_raw/source_metadata_raw.csv \
  --output empirical/megachile_leaf_resource/data_raw/source_metadata_deduplicated.csv \
  --audit-output empirical/megachile_leaf_resource/data_raw/source_metadata_duplicate_audit.csv
```

Add legally obtained, reviewable source text as one UTF-8 file per source:

```text
data_raw/source_text/<source_id>.txt
```

Then make packets for an LLM or manual review:

```bash
python empirical/megachile_leaf_resource/scripts/04_prepare_review_packets.py \
  --metadata empirical/megachile_leaf_resource/data_raw/source_metadata_deduplicated.csv \
  --text-dir empirical/megachile_leaf_resource/data_raw/source_text \
  --output-dir empirical/megachile_leaf_resource/data_raw/review_packets
```

Copy only reviewed candidate records into `data_raw/host_evidence_ledger.csv`, based on `host_evidence_template.csv`. Validate before building a host universe:

```bash
python empirical/megachile_leaf_resource/scripts/05_validate_host_evidence.py \
  --input empirical/megachile_leaf_resource/data_raw/host_evidence_ledger.csv \
  --output empirical/megachile_leaf_resource/data_processed/host_evidence_validated.csv \
  --fail-on-errors

python empirical/megachile_leaf_resource/scripts/06_build_primary_host_universe.py \
  --input empirical/megachile_leaf_resource/data_processed/host_evidence_validated.csv \
  --output empirical/megachile_leaf_resource/data_processed/primary_host_universe.csv
```

## Metadata providers

Crossref is the default because its REST API is public and does not require a sign-up. OpenAlex may be added with `--provider both`, but requires an API key under its current access policy. Neither provider is a full-text or interaction database. Metadata hits are search leads only.

## Non-negotiable review rule

A model may extract a candidate statement. A person must verify the quoted evidence and locator before setting `include_in_primary_host_universe=TRUE`.
