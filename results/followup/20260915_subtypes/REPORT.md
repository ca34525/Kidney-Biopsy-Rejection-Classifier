# Rejection subtype follow-up

## Main result

This follow-up compares four-class CatBoost and multinomial logistic regression with the existing separate component models. All models score the same specimens directly, including specimens whose binary rejection flag is negative.

| Model | Correct diagnosis / 345 | Macro F1 | Mixed correctly named / 18 | Any-rejection misses / 169 | False rejection flags / 176 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Four-class CatBoost | 281 | 0.725 | 7 | 29 | 8 |
| Four-class logistic | 283 | 0.760 | 10 | 28 | 10 |
| Separate components | 284 | 0.737 | 10 | 24 | 15 |
| Binary CatBoost benchmark | — | — | — | 25 | 8 |

The separate component models correctly named 10 of the 18 mixed diagnoses; four-class CatBoost named 7 and logistic regression named 10. The corresponding numbers of non-mixed specimens incorrectly called mixed were 13, 6, and 5, respectively.

For any rejection, four-class CatBoost missed 29 specimens and falsely flagged 8; four-class logistic regression missed 28 and falsely flagged 10. The original binary model missed 25 and falsely flagged 8. These counts describe the observed tradeoff at each discovery-selected threshold; the four-class comparison supplies no new independent evaluation cohort.

The four-class diagnosis uses the highest class score. Its any-rejection flag instead uses the sum of all three rejection-class scores and a separately frozen threshold. Those are different decisions; predicting an incorrect rejection subtype need not mean missing rejection altogether.

## What changed, and what the comparison can establish

The primary binary model remains the research service model. These subtype results describe an additional label task; they do not replace the binary model or its threshold. This is follow-up analysis because the authors' technical-validation cohort was examined in earlier project work. No validation result selected a candidate or changed a threshold in this run. Independent confirmation requires a new cohort.

## Discovery selection

Five candidates were fixed before fitting: four-class CatBoost with depths 4 and 6, 300 trees, learning rate 0.04 and seed 2026; and full-panel multinomial logistic regression with C = 0.01, 0.1, and 1. StandardScaler was fitted on training rows only. The logistic model uses the multinomial loss with the lbfgs solver, as described in the [scikit-learn documentation](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html).

Within each family, maximize discovery-screen macro F1 (the mean of each diagnosis's F1), then accuracy; exact ties favor lower depth or stronger regularization. This weights mixed rejection equally in selection even though it is uncommon. The selected fitted model is retained without refitting. The entire bounded candidate grid is in `configuration.json`; all screening results are in `candidate_screen.csv`.

- Four-class CatBoost: **catboost_depth6**, discovery macro F1 0.789; any-rejection threshold 0.815289680564.
- Four-class logistic: **logistic_C0.01**, discovery macro F1 0.799; any-rejection threshold 0.747452902756.

Each sum-of-rejection threshold is the highest screening score that retains at least 90% of screening rejection cases, matching the original binary operating rule. Antibody and T-cell marginal-score thresholds use that same rule on their own component labels. Threshold selection does not establish probability calibration; outputs remain model scores. Separate-component thresholds and models are preserved from the benchmark run.

## Same specimens and preprocessing

| Split | No rejection | Antibody-mediated | T-cell-mediated | Mixed | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 267 | 207 | 256 | 57 | 787 |
| discovery_screen | 89 | 69 | 86 | 19 | 263 |
| author_validation | 176 | 56 | 95 | 18 | 345 |

The raw GSE212160 RCC measurements are read through the shared source reader. Each specimen is transformed by log2(count + 1), then subtracting its mean across the 12 housekeeping targets. The remaining 758 assay targets are used in the frozen order. Recorded diagnoses, cohort, specimen IDs, and assay batch fields are excluded from predictors. The saved split is matched by specimen ID, checked against the source diagnoses and author cohorts, and checked against the exact seed-20260915 diagnosis-stratified split. The original raw files, saved split, frozen benchmark metadata and model files are hash-verified before use. See `data_audit.json`.

## Per-class results on technical validation

Sensitivity means the fraction of that recorded diagnosis correctly named. Precision means the fraction of that predicted diagnosis that was correct. Intervals are 95% Wilson intervals over biopsy specimens; patient independence is not established.

| Model | Diagnosis | Correct / actual | Predicted | Sensitivity (95% interval) | Precision (95% interval) |
| --- | --- | ---: | ---: | --- | --- |
| Four-class CatBoost | No Rejection | 154/176 | 173 | 87.5% (81.8%–91.6%) | 89.0% (83.5%–92.9%) |
| Four-class CatBoost | Antibody-mediated Rejection | 47/56 | 59 | 83.9% (72.2%–91.3%) | 79.7% (67.7%–88.0%) |
| Four-class CatBoost | T cell-mediated Rejection | 73/95 | 100 | 76.8% (67.4%–84.2%) | 73.0% (63.6%–80.7%) |
| Four-class CatBoost | Mixed Rejection | 7/18 | 13 | 38.9% (20.3%–61.4%) | 53.8% (29.1%–76.8%) |
| Four-class logistic | No Rejection | 155/176 | 174 | 88.1% (82.4%–92.1%) | 89.1% (83.6%–92.9%) |
| Four-class logistic | Antibody-mediated Rejection | 46/56 | 60 | 82.1% (70.2%–90.0%) | 76.7% (64.6%–85.6%) |
| Four-class logistic | T cell-mediated Rejection | 72/95 | 96 | 75.8% (66.3%–83.3%) | 75.0% (65.5%–82.6%) |
| Four-class logistic | Mixed Rejection | 10/18 | 15 | 55.6% (33.7%–75.4%) | 66.7% (41.7%–84.8%) |
| Separate components | No Rejection | 161/176 | 185 | 91.5% (86.4%–94.8%) | 87.0% (81.4%–91.1%) |
| Separate components | Antibody-mediated Rejection | 43/56 | 54 | 76.8% (64.2%–85.9%) | 79.6% (67.1%–88.2%) |
| Separate components | T cell-mediated Rejection | 70/95 | 83 | 73.7% (64.0%–81.5%) | 84.3% (75.0%–90.6%) |
| Separate components | Mixed Rejection | 10/18 | 23 | 55.6% (33.7%–75.4%) | 43.5% (25.6%–63.2%) |

All four-by-four counts, including zeros, are in `confusion_matrices.csv` and the [editable confusion chart](figures/01_subtype_confusion.svg).

## Mixed rejection

| Model | Predicted none | Predicted antibody only | Predicted T-cell only | Predicted mixed |
| --- | ---: | ---: | ---: | ---: |
| Four-class CatBoost | 0 | 5 | 6 | 7 |
| Four-class logistic | 0 | 4 | 4 | 10 |
| Separate components | 0 | 5 | 3 | 10 |

The separate-component prediction is mixed only when both preserved component flags are positive; antibody only and T-cell only require the corresponding flag alone. Neither flag produces no rejection. This is a direct four-diagnosis comparison and does not assume the two component scores are independent probabilities. For four-class models, `component_metrics.csv` also evaluates antibody-plus-mixed and T-cell-plus-mixed score sums with discovery-chosen component thresholds. The distinction shows whether a mixed specimen is missing one component or whether the four-way choice assigned it to a single-component diagnosis. Only 18 validation specimens have mixed rejection; the intervals above reflect the limited number.

## Any-rejection comparison

| Model | Threshold | Sensitivity | Specificity | Misses | False flags | Misses minus binary | False flags minus binary |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Four-class CatBoost | 0.815290 | 82.8% | 95.5% | 29 | 8 | +4 | +0 |
| Four-class logistic | 0.747453 | 83.4% | 94.3% | 28 | 10 | +3 | +2 |
| Binary CatBoost | 0.876588 | 85.2% | 95.5% | 25 | 8 | +0 | +0 |
| Separate components | Either component flag | 85.8% | 91.5% | 24 | 15 | -1 | +7 |

The 90% sensitivity setting applied to discovery screening; it does not guarantee 90% sensitivity in technical validation. `any_rejection_metrics.csv` includes screening and validation counts, intervals, precision, negative predictive value, ROC-AUC, and average precision. No single continuous any-rejection score is asserted for the union of the two separate component flags, so its ROC-AUC and average precision are left undefined. `any_errors_by_diagnosis.csv` separates false flags and misses by the original diagnosis. `paired_error_differences.csv` contains paired specimen-bootstrap intervals for differences in missed rejection and false flags, with 2,000 resamples and seed 20260915. These are descriptive specimen intervals, not evidence of patient-level independence.

## Reproduce and inspect

From the project root:

```powershell
uv sync --locked
uv run python scripts/verify_local_data.py
uv run python experiments/rejection_subtypes/run.py
```

For a clean checkout, run the documented download and binary-reproduction commands first. This follow-up uses the independently generated `results/reproduction/20260915_shared` run and `data/processed/models/20260915_shared` models. Populated local inputs need no download. Completed outputs are never overwritten: set fresh `--output-dir`, `--model-dir`, and `--case-dir` for another run. Use `--benchmark-run` and `--benchmark-models` to name another fixed reproduction.

This run fitted five candidates in 117.3 seconds including input verification, fitting, evaluation and chart preparation. `run_manifest.json` records exact elapsed time, package versions, input/output hashes, source snapshots and the lockfile used at run start. `frozen.json` was written before technical-validation predictions. New model save/reload scores agree within an absolute tolerance of 1e-12, with actual maximum differences in `verification.json`; benchmark scores also reproduce their saved prediction tables within that tolerance.

Editable evidence: [confusion matrices](figures/01_subtype_confusion.svg), [any-rejection errors](figures/02_any_rejection_errors.svg), and [mixed-rejection predictions](figures/03_mixed_rejection.svg). Each has a PNG and an aggregate CSV. Per-specimen scores and error tables are kept only in the ignored case directory, and fitted models only in the ignored model directory.
