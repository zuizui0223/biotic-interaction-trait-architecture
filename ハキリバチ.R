
library(rgbif)
library(dplyr)
library(purrr)
library(tibble)

fetch_occ_japan <- function(sp){
  
  message("Fetching: ", sp)
  
  tryCatch({
    dat <- rgbif::occ_search(
      scientificName = sp,
      country = "JP",
      hasCoordinate = TRUE,
      limit = 200000
    )$data
    
    if (is.null(dat) || nrow(dat) == 0) return(NULL)
    
    dat <- dat %>%
      filter(!is.na(decimalLongitude),
             !is.na(decimalLatitude),
             decimalLongitude != 0,
             decimalLatitude != 0) %>%
      distinct(decimalLongitude, decimalLatitude, .keep_all = TRUE)
    
    if (nrow(dat) == 0) return(NULL)
    
    tibble(
      species = sp,
      lon = dat$decimalLongitude,
      lat = dat$decimalLatitude
    )
    
  }, error = function(e){
    message("Error for ", sp, ": ", e$message)
    return(NULL)
  })
}



leaf_final12 <- c(
  "Calystegia sepium",
  "Lotus corniculatus",
  "Trifolium repens",
  "Lythrum salicaria",
  "Hypochaeris radicata",
  "Rubus crataegifolius",
  "Lamium purpureum",
  "Anaphalis margaritacea",
  "Rosa multiflora",
  "Cornus controversa",
  "Acer palmatum",
  "Cosmos bipinnatus"
)


gbif_leaf_list12 <- map(leaf_final12, fetch_japan_occ)


gbif_leaf_list12 <- gbif_leaf_list12[!sapply(gbif_leaf_list12, is.null)]


for(i in seq_along(gbif_leaf_list12)){
  gbif_leaf_list12[[i]]$species <- leaf_final12[i]
}

# まとめる（.id を使わない）
leaf_occ12 <- dplyr::bind_rows(gbif_leaf_list12)

# 確認
table(leaf_occ12$species)


ssdm_leaf12 <- stack_modelling(
  algorithms   = c("GLM","RF"),
  Occurrences  = as.data.frame(leaf_occ12),
  Env          = Env_r,
  Xcol         = "lon",
  Ycol         = "lat",
  Spcol        = "species",
  rep          = 1,
  cores        = 8,
  verbose      = TRUE
)
plot(ssdm_leaf12@diversity.map, main="Leaf Resource Diversity (12 species)")


library(rgbif)
library(dplyr)

# Megachile の GBIF taxonKey
key <- name_backbone(name="Megachile")$usageKey

# 日本の Megachile の occurrence から種一覧
meg_jp_gbif <- occ_search(
  taxonKey = key,
  country = "JP",
  limit = 3000,
  fields = c("species", "speciesKey")
)

# 種リスト
jp_species <- meg_jp_gbif$data %>% 
  filter(!is.na(species)) %>% 
  distinct(species, speciesKey)

jp_specie

get_gbif_japan <- function(key){
  occ_search(
    taxonKey = key,
    country = "JP",
    limit = 200000,   # 安全に大量取得できる
    fields = c("species", "decimalLongitude", "decimalLatitude")
  )$data
}

# 28 種をまとめて取得
gbif_meg_jp <- map_dfr(jp_species$speciesKey, get_gbif_japan)

gbif_meg_jp_clean <- gbif_meg_jp %>%
  filter(!is.na(decimalLongitude), !is.na(decimalLatitude)) %>%
  distinct(species, decimalLongitude, decimalLatitude)

library(dplyr)
library(tidyr)
library(SSDM)
library(terra)
library(purrr)

# -------------------------
# 1. 20件以上の種を抽出
# -------------------------
occ_counts <- gbif_meg_jp_clean %>%
  count(species, name = "n_occ")

target_species <- occ_counts %>%
  filter(n_occ >= 20) %>%
  pull(species)

# -------------------------
# 2. SSDM 用 Occ データ
# -------------------------
meg_occ <- gbif_meg_jp_clean %>%
  filter(species %in% target_species) %>%
  transmute(
    lon = decimalLongitude,
    lat = decimalLatitude,
    species = species
  )

# 確認
head(meg_occ)


ssdm_meg <- stack_modelling(
  algorithms   = c("GLM","RF"),
  Occurrences  = as.data.frame(meg_occ),
  Env          = Env_r,
  Xcol         = "lon",
  Ycol         = "lat",
  Spcol        = "species",
  rep          = 1,
  cores        = 8,
  verbose      = TRUE
)

plot(ssdm_meg@diversity.map, main="Megachile Diversity (>=20 occurrences)")
par(mfrow=c(3,3))
for(n in names(ssdm_meg@esdms)){
  m <- ssdm_meg@esdms[[n]]
  plot(m@projection, main=n)
}


library(dplyr)
library(tidyr)
library(readr)
library(tibble)
library(ggplot2)

# TRY txt
try_raw <- read_delim(
  "/Users/zui/Desktop/45613_04122025093830/45613.txt",
  show_col_types = FALSE
)
leaf_final12 <- c(
  "Calystegia sepium",
  "Lotus corniculatus",
  "Trifolium repens",
  "Lythrum salicaria",
  "Hypochaeris radicata",
  "Rubus crataegifolius",
  "Lamium purpureum",
  "Anaphalis margaritacea",
  "Rosa multiflora",
  "Cornus controversa",
  "Acer palmatum",
  "Cosmos bipinnatus"
)
try_sub <- try_raw %>%
  filter(AccSpeciesName %in% leaf_final12)
normalize_trait <- function(name){
  name <- tolower(name)
  
  if (grepl("specific leaf area|sla|1/lma", name)) return("SLA")
  if (grepl("leaf dry matter content", name)) return("LDMC")
  if (grepl("leaf water content", name)) return("Leaf water content")
  if (grepl("leaf thickness", name)) return("Leaf thickness")
  if (grepl("leaf density", name)) return("Leaf density")
  if (grepl("leaf area", name)) return("Leaf area")
  
  return(NA)
}

try_trait_table2 <- try_sub %>%
  mutate(TraitSimple = sapply(TraitName, normalize_trait)) %>%
  filter(!is.na(TraitSimple)) %>%              # 分類不能な trait を除外
  group_by(AccSpeciesName, TraitSimple) %>%
  summarise(mean_value = mean(StdValue, na.rm = TRUE), .groups = "drop")
trait_mat <- try_trait_table2 %>%
  pivot_wider(
    names_from = TraitSimple,
    values_from = mean_value
  ) %>%
  column_to_rownames("AccSpeciesName")

trait_mat_clean <- trait_mat %>%
  mutate(across(everything(), as.numeric))

pca <- prcomp(na.omit(trait_mat_clean), scale. = TRUE)

pca_df <- data.frame(pca$x, species = rownames(pca$x))

ggplot(pca_df, aes(PC1, PC2, label = species)) +
  geom_point(size=4) +
  geom_text(vjust = -0.4) +
  theme_minimal()



library(dplyr)
library(tidyr)
library(readr)
library(tibble)
library(purrr)
library(terra)
library(SSDM)
library(ecospat)
try_raw <- read_delim(
  "/Users/zui/Desktop/45613_04122025093830/45613.txt",
  show_col_types = FALSE
)

leaf_final12 <- c(
  "Calystegia sepium", "Lotus corniculatus", "Trifolium repens",
  "Lythrum salicaria", "Hypochaeris radicata", "Rubus crataegifolius",
  "Lamium purpureum", "Anaphalis margaritacea", "Rosa multiflora",
  "Cornus controversa", "Acer palmatum", "Cosmos bipinnatus"
)

try_sub <- try_raw %>%
  filter(AccSpeciesName %in% leaf_final12)

normalize_trait <- function(name){
  name <- tolower(name)
  if (grepl("specific leaf area|sla|1/lma", name)) return("SLA")
  if (grepl("leaf dry matter content", name)) return("LDMC")
  if (grepl("leaf water content", name)) return("Leaf water content")
  if (grepl("leaf thickness", name)) return("Leaf thickness")
  if (grepl("leaf density", name)) return("Leaf density")
  if (grepl("leaf area", name)) return("Leaf area")
  return(NA)
}

try_trait_table2 <- try_sub %>%
  mutate(TraitSimple = sapply(TraitName, normalize_trait)) %>%
  filter(!is.na(TraitSimple)) %>%
  group_by(AccSpeciesName, TraitSimple) %>%
  summarise(mean_value = mean(StdValue, na.rm = TRUE), .groups="drop")

leaf_traits <- try_trait_table2 %>%
  pivot_wider(
    names_from  = TraitSimple,
    values_from = mean_value
  ) %>%
  column_to_rownames("AccSpeciesName") %>%
  mutate(across(everything(), as.numeric))
leaf_esdms <- ssdm_leaf12@esdms
leaf_rasters <- lapply(leaf_esdms, function(m) rast(m@projection))
names(leaf_rasters) <- gsub("\\.Ensemble\\.SDM$", "", names(leaf_esdms))

bee_esdms <- ssdm_meg@esdms
bee_rasters <- lapply(bee_esdms, function(m) rast(m@projection))
names(bee_rasters) <- gsub("\\.Ensemble\\.SDM$", "", names(bee_esdms))
common_leaf <- intersect(names(leaf_rasters), rownames(leaf_traits))

leaf_traits_sub <- leaf_traits[common_leaf, , drop=FALSE]
leaf_rasters_sub <- leaf_rasters[common_leaf]
calc_bee_trait_centroid <- function(bee_name, bee_rasters, leaf_rasters_sub, leaf_traits_sub){
  
  r_bee <- bee_rasters[[bee_name]]
  
  out <- rep(NA_real_, ncol(leaf_traits_sub))
  names(out) <- colnames(leaf_traits_sub)
  
  overlap_vec <- numeric(length(leaf_rasters_sub))
  names(overlap_vec) <- names(leaf_rasters_sub)
  
  for (sp in names(leaf_rasters_sub)) {
    r_leaf <- leaf_rasters_sub[[sp]]
    r_leaf <- terra::resample(r_leaf, r_bee)
    
    prod_rl <- r_bee * r_leaf
    overlap_vec[sp] <- as.numeric(terra::global(prod_rl, "sum", na.rm = TRUE))
  }
  
  if (all(overlap_vec <= 0 | is.na(overlap_vec))) return(out)
  
  w <- overlap_vec / sum(overlap_vec, na.rm = TRUE)
  
  for (tr in colnames(leaf_traits_sub)) {
    out[tr] <- sum(leaf_traits_sub[, tr] * w, na.rm = TRUE)
  }
  
  out
}

bee_names_clean <- names(bee_rasters)

bee_trait_mat <- t(
  sapply(
    bee_names_clean,
    function(bnm){
      calc_bee_trait_centroid(
        bee_name        = bnm,
        bee_rasters     = bee_rasters,
        leaf_rasters_sub = leaf_rasters_sub,
        leaf_traits_sub  = leaf_traits_sub
      )
    }
  )
)

bee_trait_df <- as.data.frame(bee_trait_mat)
bee_trait_df$BeeSpecies <- rownames(bee_trait_df)
bee_trait_df
cor_mat <- matrix(nrow=length(bee_names_clean), ncol=length(bee_names_clean))
rownames(cor_mat) <- colnames(cor_mat) <- bee_names_clean

for(i in 1:length(bee_names_clean)){
  for(j in 1:length(bee_names_clean)){
    r1 <- values(bee_rasters[[i]])
    r2 <- values(bee_rasters[[j]])
    cor_mat[i,j] <- cor(r1, r2, use="pairwise.complete.obs")
  }
}

cor_mat



install.packages("hypervolume")

library(hypervolume)
library(tidyverse)
library(ks)
leaf_traits_filled <- leaf_traits_sub

for(col in colnames(leaf_traits_filled)){
  if(is.numeric(leaf_traits_filled[[col]])){
    mean_val <- mean(leaf_traits_filled[[col]], na.rm = TRUE)
    leaf_traits_filled[[col]][is.na(leaf_traits_filled[[col]])] <- mean_val
  }
}
calc_bee_overlap <- function(bee_name, bee_rasters, leaf_rasters_sub){
  r_bee <- bee_rasters[[bee_name]]
  
  overlap_vec <- numeric(length(leaf_rasters_sub))
  names(overlap_vec) <- names(leaf_rasters_sub)
  
  for (sp in names(leaf_rasters_sub)) {
    r_leaf <- leaf_rasters_sub[[sp]]
    r_leaf <- terra::resample(r_leaf, r_bee)
    
    prod_rl <- r_bee * r_leaf
    overlap_val <- as.numeric(terra::global(prod_rl, "sum", na.rm = TRUE))
    overlap_vec[sp] <- overlap_val
  }
  
  return(overlap_vec)
}

overlap_weights_list <- lapply(
  bee_names_clean,
  function(bnm){
    calc_bee_overlap(bnm, bee_rasters, leaf_rasters_sub)
  }
)
names(overlap_weights_list) <- bee_names_clean
leaf_list <- lapply(1:nrow(leaf_traits_filled), function(i){
  as.numeric(leaf_traits_filled[i, ])
})
names(leaf_list) <- rownames(leaf_traits_filled)

compute_weighted_hv <- function(leaf_list, weight_vec, n_sample = 5000){
  
  w <- weight_vec + 1e-6
  w_norm <- w / sum(w)
  
  n_per_species <- round(w_norm * n_sample)
  if(all(n_per_species == 0)){
    n_per_species[which.max(w_norm)] <- 1
  }
  
  trait_points_list <- mapply(
    function(tr_vec, n){
      if(n <= 0) return(NULL)
      matrix(rep(tr_vec, each = n), ncol = length(tr_vec))
    },
    tr_vec = leaf_list,
    n = n_per_species,
    SIMPLIFY = FALSE
  )
  
  trait_points <- do.call(rbind, trait_points_list)
  colnames(trait_points) <- colnames(leaf_traits_filled)
  
  bw <- estimate_bandwidth(trait_points, method = "silverman")
  
  hv <- hypervolume_gaussian(
    data = trait_points,
    kde.bandwidth = bw,
    name = "utilization_hypervolume"
  )
  
  return(hv)
}
bee_hv_list <- list()

for(bnm in bee_names_clean){
  w <- overlap_weights_list[[bnm]]
  
  hv <- compute_weighted_hv(
    leaf_list   = leaf_list,
    weight_vec  = w,
    n_sample    = 5000
  )
  
  bee_hv_list[[bnm]] <- hv
}
sapply(bee_hv_list, get_volume)

hv_centroid <- function(hv){
  apply(hv@Data, 2, mean)
}

centroids <- lapply(bee_hv_list, hv_centroid)

dist_centroid <- dist(do.call(rbind, centroids))
as.matrix(dist_centroid)
df_pca <- lapply(names(bee_hv_list), function(name){
  data.frame(bee = name, bee_hv_list[[name]]@Data)
}) %>% bind_rows()

pr <- prcomp(df_pca[, -1], scale. = TRUE)

plot(pr$x[,1], pr$x[,2], col = as.factor(df_pca$bee), pch = 19)
legend("topright", legend = unique(df_pca$bee), col = 1:length(bee_names_clean), pch = 19)
hv_dist <- function(hv1, hv2){
  H1 <- Hscv(hv1@Data)
  H2 <- Hscv(hv2@Data)
  d <- Hdist(H1, H2)
  return(d)
}

pair_dist <- outer(bee_names_clean, bee_names_clean, Vectorize(function(a,b){
  hv_dist(bee_hv_list[[a]], bee_hv_list[[b]])
}))





# PCA on leaf traits
pr_leaf <- prcomp(leaf_traits_filled, scale. = TRUE)

# PCA scores for species (the leaves)
pca_leaf_scores <- data.frame(pr_leaf$x)
pca_leaf_scores$plant <- rownames(leaf_traits_filled)
# convert centroids to matrix
cent_mat <- do.call(rbind, centroids)

# project centroids into PCA space
centroid_pca <- scale(cent_mat, pr_leaf$center, pr_leaf$scale) %*% pr_leaf$rotation
centroid_pca <- as.data.frame(centroid_pca)
centroid_pca$bee <- rownames(cent_mat)
library(ggplot2)

ggplot() +
  # plant species points
  geom_point(
    data = pca_leaf_scores,
    aes(PC1, PC2), size = 3, color = "black"
  ) +
  geom_text(
    data = pca_leaf_scores,
    aes(PC1, PC2, label = plant),
    vjust = -1, size = 3
  ) +
  
  # bee centroid points
  geom_point(
    data = centroid_pca,
    aes(PC1, PC2, color = bee),
    size = 4
  ) +
  
  geom_text(
    data = centroid_pca,
    aes(PC1, PC2, label = bee, color = bee),
    vjust = -1, size = 3
  ) +
  
  # arrows from global centroid (mean leaf trait) to bee centroid
  geom_segment(
    data = centroid_pca,
    aes(
      x = 0, y = 0,
      xend = PC1, yend = PC2,
      color = bee
    ),
    arrow = arrow(length = unit(0.25, "cm")),
    size = 1
  ) +
  
  theme_minimal(base_size = 14) +
  labs(
    title = "Bee-specific trait-niche shifts in PCA space",
    x = "PC1 (Leaf size–SLA gradient)",
    y = "PC2 (Leaf density gradient)"
  )

library(ecodist)

# 正規化（行＝ハチ種、列＝植物）
use_norm <- bee_use_matrix / rowSums(bee_use_matrix)

# Schoener's D 計算（1 - 0.5 * Σ|p_i - q_i|）
schoenerD <- function(p, q){
  1 - 0.5 * sum(abs(p - q))
}

bee_names <- rownames(use_norm)
Dmat <- matrix(NA, nrow = length(bee_names), ncol = length(bee_names),
               dimnames = list(bee_names, bee_names))

for(i in 1:nrow(use_norm)){
  for(j in 1:nrow(use_norm)){
    Dmat[i, j] <- schoenerD(use_norm[i, ], use_norm[j, ])
  }
}

Dmat












