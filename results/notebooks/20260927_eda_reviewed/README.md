# Executed notebook evidence — September 27, 2026

The three notebooks completed in fresh Python 3.12 kernels using this project's
raw public inputs and the preserved `20260915_shared` model run. These notebooks
were added after the presentation. They do not retrain models or change thresholds.

## Browser views

1. [Data quality and preprocessing](01_data_quality_and_preprocessing.html)
2. [Exploratory data analysis](02_exploratory_data_analysis.html)
3. [Model comparison and RNA contributions](03_model_comparison_and_rna_contributions.html)

Editable notebooks are in [the notebook directory](../../../notebooks/README.md).
This folder preserves their source snapshots and executed copies. Each notebook's
subdirectory contains aggregate tables, PNG/SVG figures, and a manifest of inputs,
settings, model version where used, source hashes, and output hashes.

## Findings

- All 1,395 specimens loaded with 770 raw targets and 758 normalized predictors.
  There were no missing counts, duplicate raw or normalized profiles, or housekeeping
  zeros.
- The descriptive 1.5 IQR rule on log total count identified 28 unusually low-total
  specimens: 23 discovery and five technical-validation specimens. They were
  retained. The notebook compares their housekeeping signal and sparsity with the
  other specimens; these measurements alone do not establish a laboratory cause.
- The first two training-fitted PCA axes explain 45.4% of training variance.
  Cohort and assay dates/cartridges remain linked.
- GBP4 leads both saved CatBoost importance and mean absolute screening SHAP.
  The next four SHAP targets are PLA1A, CCL19, HLA-B, and CXCL11. These are contributions
  to the fitted model, not causal biological effects.
- The preserved validation errors reproduce: CatBoost missed 25/169 rejection
  cases and flagged 8/176 no-rejection specimens; logistic missed 33 with eight
  false flags.

## Verification

- [Execution record](execution.json): 39 code cells, three fresh kernels.
- Seventeen figures embedded in the notebooks and exported as PNG/SVG.
- No cell errors or stderr outputs in the reviewed notebooks.
- Model scores agree with saved predictions within absolute tolerance 1e-10.
  Frozen flags agree exactly. Screening thresholds reproduce within 1e-12.
- CatBoost SHAP contributions reconstruct both raw and 0–1 scores within 1e-10.
- [Software check record](../../checks/20260927_notebooks/checks.json): 109 tests passed.
  Ruff lint and formatting also passed, including the notebook sources.

The notebooks explain probability calibration, correlated targets, viral signals,
and the limits of the available metadata. Full specimen tables remain in memory.
