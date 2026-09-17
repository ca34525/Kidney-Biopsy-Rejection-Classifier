# Kidney biopsy training results

Run completed on September 15, 2026. All models, predictions, and metrics below
were generated in this project from its own local raw public inputs.

## Main finding

On the 345-specimen author technical-validation cohort, the selected CatBoost
model missed 25 of 169 rejection cases and falsely flagged 8 of 176
non-rejection cases. The multivariable logistic model missed 33 cases with
the same number of false flags. At their discovery-selected thresholds, CatBoost
therefore detected 8 additional rejection cases in this comparison.

| Model | ROC-AUC | Accuracy | Missed rejection | False flags | Sensitivity | Specificity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CatBoost | 0.969 | 90.4% | 25 | 8 | 85.2% | 95.5% |
| Multivariable logistic regression | 0.956 | 88.1% | 33 | 8 | 80.5% | 95.5% |
| IFNG model | 0.842 | 74.2% | 14 | 75 | 91.7% | 57.4% |
| Training-majority baseline | 0.500 | 49.0% | 0 | 176 | 100.0% | 0.0% |

Compared with IFNG, CatBoost produced 67 fewer false flags and missed
11 additional rejection cases. These counts make the threshold tradeoff visible.

## Procedure

The run used 1,395 GSE212160 specimens, with 787 for training, 263 for screening,
and 345 for evaluation. Normalization used each specimen's 12 housekeeping
targets and retained 758 assay predictors. The target is any recorded rejection
versus no rejection in an already obtained biopsy.

Screening selected catboost_all_depth4, using 300 trees, depth 4, learning rate 0.04,
and seed 2026. Its threshold is 0.8765880870219778. Thresholds aimed for at least
90% screening sensitivity; evaluation sensitivity is shown above. The fitted
model was retained after threshold selection.

The full run fitted 27 models across the primary and two component targets
in 120.56 seconds. [All results](biopsy_results.json), [screening scores](biopsy_screen.csv),
and the [run manifest](run_manifest.json) record configurations, package versions,
input references, and artifact hashes.

## Reproduction check

A separate prediction command reloaded the newly trained model and recomputed all
345 evaluation scores. The maximum absolute score difference was 0.0.
The [verification record](inference_verification.json) records the exact comparison.
Input smoke checks covered reordered columns, missing and duplicate targets,
non-finite and negative counts, duplicate specimen IDs, and empty input. Prediction
also rejects a mismatched model directory.

## Interpretation

The result concerns agreement with recorded histological diagnoses in this study.
It does not measure improved patient outcomes. Patient and center independence
are unverified. These limits inform the next study; the immediate project work is
to explain the comparison and package the model in a usable research demonstration.

Raw inputs, models, and per-specimen tables remain local and Git-ignored.
