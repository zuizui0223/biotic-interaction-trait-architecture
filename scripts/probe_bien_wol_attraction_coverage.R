# Test whether BIEN can supply non-circular attraction proxies for Web of Life
# pollination networks after plant--animal orientation.
#
# Input: an `orientation/` directory emitted by probe_wol_orientation.py.
# Output: taxon-level coverage rows plus a source-contract decision.
#
# This is a screening test only. It samples one already-oriented plant taxon
# from each of 30 networks. A pass advances to full network-level coverage;
# it does not establish ecological inference or validate a trait's mechanism.

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) {
  stop(
    "usage: Rscript scripts/probe_bien_wol_attraction_coverage.R orientation_dir out_dir",
    call. = FALSE
  )
}

orientation_dir <- args[[1]]
out_dir <- args[[2]]
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

write_report <- function(report) {
  jsonlite::write_json(
    report,
    file.path(out_dir, "bien_wol_attraction_coverage_report.json"),
    pretty = TRUE,
    auto_unbox = TRUE
  )
  cat(jsonlite::toJSON(report, pretty = TRUE, auto_unbox = TRUE), "\n")
}

if (!requireNamespace("BIEN", quietly = TRUE)) {
  write_report(list(
    source = "BIEN + Web of Life",
    access_status = "package_unavailable",
    decision = "reject_BIEN_as_automated_attraction_trait_backbone_and_pivot"
  ))
  quit(status = 0)
}

orientation_path <- file.path(orientation_dir, "wol_orientation_network_audit.csv")
if (!file.exists(orientation_path)) {
  write_report(list(
    source = "BIEN + Web of Life",
    access_status = "orientation_input_missing",
    decision = "repair_orientation_dependency_before_trait_test"
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

orientation$plant_taxon <- vapply(
  seq_len(nrow(orientation)),
  function(index) plant_from_row(orientation[index, , drop = FALSE]),
  character(1)
)
orientation <- orientation[!is.na(orientation$plant_taxon), , drop = FALSE]

# Stable random sampling avoids an alphabetical regional or taxonomic cluster.
set.seed(20260629)
sample_size <- min(30L, nrow(orientation))
if (sample_size == 0L) {
  write_report(list(
    source = "BIEN + Web of Life",
    access_status = "no_oriented_plant_taxa",
    decision = "reject_or_repair_orientation_dependency_before_trait_test"
  ))
  quit(status = 0)
}
selected <- orientation[sample(seq_len(nrow(orientation)), sample_size), , drop = FALSE]

# `flower pollination syndrome` is intentionally excluded: it encodes the
# interaction domain that the model is meant to predict. Flowering phenology is
# recorded by BIEN but is not a direct display proxy. This first test retains
# only a categorical visual signal and a display-extent proxy.
traits <- c("flower color", "inflorescence length")

query_one <- function(species, trait) {
  result <- tryCatch(
    BIEN::BIEN_trait_traitbyspecies(species = species, trait = trait),
    error = function(error) error
  )
  if (inherits(result, "error")) {
    return(list(status = "query_error", records = 0L, message = conditionMessage(result)))
  }
  if (!is.data.frame(result)) {
    return(list(status = "unexpected_result", records = 0L, message = class(result)[[1]]))
  }
  list(
    status = if (nrow(result) > 0) "trait_record_found" else "no_trait_record",
    records = nrow(result),
    message = ""
  )
}

coverage_rows <- list()
for (trait in traits) {
  for (index in seq_len(nrow(selected))) {
    species <- selected$plant_taxon[[index]]
    outcome <- query_one(species, trait)
    coverage_rows[[length(coverage_rows) + 1L]] <- data.frame(
      network_name = selected$network_name[[index]],
      orientation = selected$orientation[[index]],
      plant_taxon = species,
      trait = trait,
      query_status = outcome$status,
      records_returned = outcome$records,
      message = outcome$message,
      stringsAsFactors = FALSE
    )
  }
}
coverage <- do.call(rbind, coverage_rows)
write.csv(
  coverage,
  file.path(out_dir, "bien_wol_attraction_coverage.csv"),
  row.names = FALSE,
  na = ""
)

trait_summary <- lapply(traits, function(trait) {
  subset <- coverage[coverage$trait == trait, , drop = FALSE]
  found <- sum(subset$query_status == "trait_record_found")
  list(
    trait = trait,
    sampled_taxa = nrow(subset),
    taxa_with_records = found,
    coverage_rate = found / nrow(subset),
    query_errors = sum(subset$query_status == "query_error")
  )
})
names(trait_summary) <- traits
usable_traits <- vapply(trait_summary, function(entry) entry$coverage_rate >= 2 / 3 && entry$query_errors == 0L, logical(1))

write_report(list(
  source = "BIEN::BIEN_trait_traitbyspecies + Web of Life pollination sample",
  sample_seed = 20260629,
  oriented_networks_available = nrow(orientation),
  sampled_networks = nrow(selected),
  non_circular_candidate_traits = traits,
  trait_summary = trait_summary,
  threshold = "At least one non-circular attraction proxy must have >= 2/3 taxon coverage with zero query errors in this 30-network screen.",
  decision = if (any(usable_traits)) {
    "advance_to_full_network_trait_coverage_test"
  } else {
    "reject_BIEN_as_automated_attraction_trait_backbone_and_pivot_to_global_trait_request"
  }
))