# BK targets and study composition

This descriptive follow-up reviews the frozen `catboost_all_depth4` model from `results/reproduction/20260922_mac_clone`. It does not fit a model, change its features, choose a new operating threshold, or diagnose infection. Re-run with `uv run python scripts/review_viral_targets.py --output-dir results/analysis/NEW_viral --specimen-dir data/processed/analysis/NEW_viral`.

## Main finding

The saved importance table ranks the two BK targets as follows: BK  large T Ag: rank 2, importance 5.04; BK  VP1: rank 3, importance 3.85. The B-HOT panel includes viral targets; these measurements are not human genes. [Banff B-HOT consensus, Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC7496585/).

Among specimens labeled no rejection, 16/356 discovery specimens and 4/176 author-validation specimens have both normalized BK signals above zero. Across both cohorts, 0 specimens labeled rejection also meet that reference. Of the 4 validation specimens above the reference, 4 received a no-rejection result; there were 0 false flags and 0 missed rejection cases. These counts describe the relationship between BK signals, recorded diagnosis, and the model's results. Importance alone does not establish the direction, the reason for the association, or an individual feature's causal contribution.

Zero is a descriptive reference for the normalized scale: `count + 1` exceeds the geometric mean of the 12 `housekeeping count + 1` values. It is not an infection cutoff or a detection limit. The reference was used after reviewing results, for description only. Full quantiles and raw-count ranges are in `signals_by_cohort_diagnosis.csv`.

## Cohort and diagnosis

Values are median normalized signal (25th to 75th percentile), using the shared specimen-level normalization. The last column counts specimens where both BK signals exceed zero.

| Cohort | Recorded diagnosis | n | BK large T Ag | BK VP1 | Both > 0 |
| --- | --- | --- | --- | --- | --- |
| Discovery | No Rejection | 356 | -5.97 (-6.52 to -5.44) | -5.30 (-5.99 to -4.66) | 16 |
| Discovery | Antibody-mediated Rejection | 276 | -6.09 (-6.67 to -5.66) | -5.02 (-5.63 to -4.61) | 0 |
| Discovery | T cell-mediated Rejection | 342 | -5.90 (-6.40 to -5.45) | -4.61 (-5.18 to -4.04) | 0 |
| Discovery | Mixed Rejection | 76 | -5.95 (-6.43 to -5.35) | -4.24 (-4.81 to -3.75) | 0 |
| Author technical validation | No Rejection | 176 | -5.93 (-6.37 to -5.48) | -5.42 (-5.85 to -4.85) | 4 |
| Author technical validation | Antibody-mediated Rejection | 56 | -5.86 (-6.34 to -5.48) | -4.99 (-5.30 to -4.57) | 0 |
| Author technical validation | T cell-mediated Rejection | 95 | -5.97 (-6.56 to -5.58) | -4.50 (-5.02 to -4.05) | 0 |
| Author technical validation | Mixed Rejection | 18 | -5.73 (-5.99 to -5.55) | -4.39 (-4.80 to -3.74) | 0 |

The broad no-rejection label may combine different non-rejection conditions. The study's Supplementary Table S3 explicitly compares its T-cell-mediated histologic class with allograft polyomavirus nephropathy samples within its NVH histologic class. The public sample metadata available here does not identify which individual specimens have that diagnosis. [Zhang et al., Supplementary Table S3](https://ars.els-cdn.com/content/image/1-s2.0-S0023683723002477-mmc5.docx).

## Selected-model errors in author validation

The table shows median normalized signals; full ranges and quantiles are in `signals_by_validation_error.csv`.

| Result | n | BK large T Ag | BK VP1 |
| --- | --- | --- | --- |
| Correct no-rejection result | 168 | -5.94 | -5.42 |
| Correct rejection flag | 144 | -5.90 | -4.57 |
| False rejection flag | 8 | -5.58 | -4.86 |
| Missed rejection | 25 | -6.33 | -5.25 |

There are 0 missed rejection cases and 0 false flags with both BK signals above zero. These aggregate comparisons describe associations and cannot assign a reason to an individual mistake. A feature-removal experiment would be separate follow-up modeling, and was not done here.

## Available metadata and limits

The GEO metadata contains title, source tissue, histology, tissue, and author cohort. It supplies no confirmed infection indicator, viral load, patient identifier, transplant-center identifier, or detailed no-rejection subtype. The parser preserves the source's `histology diganosis of rejection` spelling and also exposes a corrected internal alias. `metadata_inventory.json` lists fields and completeness. [GSE212160 deposit](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212160).

The RCC headers expose assay metadata. Discovery uses 37 assay dates and 96 cartridges; validation uses 7 dates and 31 cartridges, with no shared dates or cartridges. All specimens use one scanner. Thus author cohort and those batches are linked; this comparison cannot separately estimate their effects. The training/screening split within discovery is a specimen split, not a held-out batch, patient, or center split. Do not infer independent patients or centers from distinct sample or cartridge identifiers.

The authors discuss extraction-protocol and sample-age comparisons in their Supplementary Methods, but those per-specimen variables are not supplied in the GEO characteristics used here. No claim about their effects is derived from these aggregate summaries. [Zhang et al., Supplementary Methods](https://ars.els-cdn.com/content/image/1-s2.0-S0023683723002477-mmc6.docx).

## Reproduction and records

Public inputs are checked against `data/manifest.json`, and used baseline artifacts are checked against the completed baseline run manifest before reading. `manifest.json` records inputs and their hashes, the shared source-code hashes, the frozen threshold, and outputs. The only specimen-level export is `data/processed/analysis/20260922_mac_clone_viral/viral_specimen_review.csv`, under ignored local data. This review uses the project's own raw RCC measurements and saved predictions; it does not use the deposited batch-corrected expression matrix as predictors. The cited supplements supply background context; local copies are optional for reproducing the numeric results, and their availability is recorded.
