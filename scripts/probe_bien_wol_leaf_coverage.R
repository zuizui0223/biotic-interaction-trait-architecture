# Probe whether the public BIEN package can return source trait rows for
# leaf-functional-trait candidates on a reproducible Web of Life plant sample.
#
# This is an availability screen, not an ecological trait-effect analysis. The
# first pass asks only whether species × trait rows can be recovered by code. A
# later receipt audit must still inspect measurement units, source provenance,
# taxonomic matching, and whether a row is suitable as a direct primary record.
#
# Usage:
#   Rscript scripts/probe_bien_wol_leaf_coverage.R orientation_dir out_dir

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) {
  stop(
    "usage: Rscript scripts/probe_bien_wol_leaf_coverage.R orientation_dir out_dir",
    call. = FALSE
  )
}

orientation_dir <- args[[1]]
out_dir <- args[[2]]
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

write_report <- function(report) {
  jsonlite::write_json(
    report,
    file.path(out_dir, "bien_wol_leaf_coverage_report.json"),
    pretty = TRUE,
    auto_unbox = TRUE,
    null = "null"
  )
  cat(jsonlite::toJSON(report, pretty = TRUE, auto_unbox = TRUE, null = "null"), "\n")
}

if (!requireNamespace("BIEN", quietly = TRUE)) {
  write_report(list(
    source = "BIEN CRAN/GitHub package + Web of Life",
    access_status = "bien_package_unavailable",
    decision = "technical_failure_repair_package_installation_before_availability_screen"
  ))
  quit(status = 1)
}

orientation_path <- file.path(orientation_dir, "wol_orientation_network_audit.csv")
if (!file.exists(orientation_path)) {
  write_report(list(
    source = "BIEN CRAN/GitHub package + Web of Life",
    access_status = "orientation_input_missing",
    decision = "repair_orientation_dependency_before_leaf_trait_test"
  ))
  quit(status = 0)
}

orientation <- read.csv(orientation_path, check.names = FALSE, stringsAsFactors = FALSE)
orientation <- orientation[
  orientation$orientation %in% c("species1_is_plant", "species2_is_plant"),
  ,
  drop = FALSE
]

plant_from_row <- function(row) {
  source_column <- if (identical(row[["orientation"]], "species1_is_plant")) {
    "species1_sample"
  } else {
    "species2_sample"
  }
  pieces <- strsplit(row[[source_column]], "; ", fixed = TRUE)[[1]]
  pieces <- trimws(pieces[nzchar(trimws(pieces))])
  if (!length(pieces)) return(NA_character_)
  pieces[[1]]
}

species_rank_binomial <- function(value) {
  if (is.na(value) || !nzchar(value)) return(FALSE)
  parts <- strsplit(trimws(value), "\\s+")[[1]]
  if (length(parts) != 2L) return(FALSE)
  if (tolower(parts[[2]]) %in% c("sp", "sp.", "spp", "spp.", "cf", "cf.", "aff", "aff.")) return(FALSE)
  grepl("^[A-Z][A-Za-z-]+ [a-z][A-Za-z-]+$", value)
}

orientation$plant_taxon <- vapply(
  seq_len(nrow(orientation)),
  function(index) plant_from_row(orientation[index, , drop = FALSE]),
  character(1)
)
orientation <- orientation[
  !is.na(orientation$plant_taxon) & vapply(orientation$plant_taxon, species_rank_binomial, logical(1)),
  ,
  drop = FALSE
]

# One taxon per network, then deterministic network sampling. This is an
# availability screen and deliberately does not let large networks dominate.
set.seed(20260629)
orientation <- orientation[!duplicated(orientation$network_name), , drop = FALSE]
sample_size <- min(30L, nrow(orientation))
if (sample_size == 0L) {
  write_report(list(
    source = "BIEN CRAN/GitHub package + Web of Life",
    access_status = "no_species_rank_plant_taxa",
    decision = "no_go_no_valid_taxa_for_leaf_trait_screen"
  ))
  quit(status = 0)
}
selected <- orientation[sample(seq_len(nrow(orientation)), sample_size), , drop = FALSE]

trait_catalogue <- tryCatch(BIEN::BIEN_trait_list(), error = function(error) error)
if (inherits(trait_catalogue, "error") || !is.data.frame(trait_catalogue)) {
  write_report(list(
    source = "BIEN::BIEN_trait_list + Web of Life",
    access_status = "trait_catalogue_query_failed",
    message = if (inherits(trait_catalogue, "error")) conditionMessage(trait_catalogue) else class(trait_catalogue)[[1]],
    decision = "technical_failure_public_trait_catalogue_unavailable"
  ))
  quit(status = 0)
}

# Trait spelling is exact and case-sensitive in BIEN queries. Discover labels
# from the live catalogue instead of relying on a frozen label dictionary.
text_columns <- names(trait_catalogue)[vapply(
  trait_catalogue,
  function(column) is.character(column) || is.factor(column),
  logical(1)
)]
all_labels <- unique(unlist(lapply(text_columns, function(column) as.character(trait_catalogue[[column]]))))
all_labels <- trimws(all_labels[nzchar(trimws(all_labels))])

trait_patterns <- list(
  sla = c("specific leaf area", "leaf area per.*dry mass", "leaf area.*dry mass"),
  ldmc = c("leaf dry matter content", "leaf dry mass per.*fresh mass", "leaf dry mass.*fresh mass"),
  leaf_n_mass = c("leaf nitrogen", "nitrogen concentration.*leaf", "nitrogen.*leaf"),
  leaf_p_mass = c("leaf phosphorus", "phosphorus concentration.*leaf", "phosphorus.*leaf"),
  leaf_thickness = c("leaf thickness")
)

find_labels <- function(patterns) {
  keep <- rep(FALSE, length(all_labels))
  for (pattern in patterns) {
    keep <- keep | grepl(pattern, all_labels, ignore.case = TRUE, perl = TRUE)
  }
  sort(unique(all_labels[keep]))
}

candidate_labels <- lapply(trait_patterns, find_labels)
candidate_table <- do.call(
  rbind,
  lapply(names(candidate_labels), function(trait_id) {
    labels <- candidate_labels[[trait_id]]
    data.frame(
      functional_trait_id = trait_id,
      bien_trait_label = if (length(labels)) labels else NA_character_,
      label_found = length(labels) > 0,
      stringsAsFactors = FALSE
    )
  })
)
write.csv(
  candidate_table,
  file.path(out_dir, "bien_leaf_trait_label_candidates.csv"),
  row.names = FALSE,
  na = ""
)

query_one <- function(species, labels) {
  if (!length(labels)) {
    return(list(status = "trait_label_not_listed", rows = 0L, columns = "", message = ""))
  }
  result <- tryCatch(
    BIEN::BIEN_trait_traitbyspecies(
      species = species,
      trait = labels,
      all.taxonomy = TRUE,
      source.citation = TRUE
    ),
    error = function(error) error
  )
  if (inherits(result, "error")) {
    return(list(status = "query_error", rows = 0L, columns = "", message = conditionMessage(result)))
  }
  if (!is.data.frame(result)) {
    return(list(status = "unexpected_result", rows = 0L, columns = "", message = class(result)[[1]]))
  }
  list(
    status = if (nrow(result) > 0) "provider_rows_found" else "no_provider_rows",
    rows = nrow(result),
    columns = paste(names(result), collapse = ";"),
    message = ""
  )
}

coverage_rows <- list()
for (trait_id in names(candidate_labels)) {
  labels <- candidate_labels[[trait_id]]
  for (index in seq_len(nrow(selected))) {
    species <- selected$plant_taxon[[index]]
    outcome <- query_one(species, labels)
    coverage_rows[[length(coverage_rows) + 1L]] <- data.frame(
      network_name = selected$network_name[[index]],
      orientation = selected$orientation[[index]],
      plant_taxon = species,
      functional_trait_id = trait_id,
      bien_trait_labels_queried = paste(labels, collapse = " | "),
      query_status = outcome$status,
      provider_rows_returned = outcome$rows,
      returned_columns = outcome$columns,
      message = outcome$message,
      stringsAsFactors = FALSE
    )
  }
}
coverage <- do.call(rbind, coverage_rows)
write.csv(
  coverage,
  file.path(out_dir, "bien_wol_leaf_trait_coverage.csv"),
  row.names = FALSE,
  na = ""
)

summary_for <- function(trait_id) {
  subset <- coverage[coverage$functional_trait_id == trait_id, , drop = FALSE]
  found <- sum(subset$query_status == "provider_rows_found")
  list(
    functional_trait_id = trait_id,
    candidate_bien_labels = candidate_labels[[trait_id]],
    sampled_taxa = nrow(subset),
    taxa_with_provider_rows = found,
    provider_row_coverage_rate = if (nrow(subset)) found / nrow(subset) else 0,
    query_errors = sum(subset$query_status == "query_error"),
    unavailable_labels = sum(subset$query_status == "trait_label_not_listed")
  )
}
trait_summary <- lapply(names(candidate_labels), summary_for)
names(trait_summary) <- names(candidate_labels)

passes_screen <- vapply(
  trait_summary,
  function(entry) {
    length(entry$candidate_bien_labels) > 0 &&
      entry$provider_row_coverage_rate >= 0.60 &&
      entry$query_errors == 0L
  },
  logical(1)
)
construction_traits <- c("sla", "ldmc", "leaf_thickness")
nutrient_traits <- c("leaf_n_mass", "leaf_p_mass")
construction_pass <- any(passes_screen[construction_traits])
nutrient_pass <- any(passes_screen[nutrient_traits])

write_report(list(
  source = "BIEN::BIEN_trait_list + BIEN::BIEN_trait_traitbyspecies + Web of Life",
  package = "BIEN",
  package_version = as.character(utils::packageVersion("BIEN")),
  sample_seed = 20260629,
  oriented_networks_with_species_rank_sample = nrow(orientation),
  sampled_networks = nrow(selected),
  result_type = "provider species-trait rows; direct-record suitability requires a later receipt audit",
  candidate_label_columns_examined = text_columns,
  trait_summary = trait_summary,
  screen_rule = paste(
    "Advance to a full receipt/coverage audit when at least one construction trait",
    "and at least one nutrient trait each show >=60% species-level provider-row coverage",
    "with zero query errors in this reproducible 30-network screen."
  ),
  decision = if (construction_pass && nutrient_pass) {
    "advance_to_full_BIEN_trait_receipt_audit"
  } else {
    "no_go_BIEN_as_current_automated_leaf_quality_provider"
  }
))
