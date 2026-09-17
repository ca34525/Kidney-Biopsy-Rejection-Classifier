# Finished analysis of the frozen primary classifier

Source run: `results/reproduction/baseline`. Analysis seed: 20260915. Target: any recorded rejection in an already collected biopsy.

## Main finding

On 345 author technical-validation specimens, CatBoost missed 25 of 169 rejection cases and falsely flagged 8 of 176 no-rejection cases. Logistic regression missed 33 with 8 false flags; IFNG missed 14 with 75 false flags. At these frozen thresholds, CatBoost detected 8 more rejection cases than logistic regression. Compared with IFNG, it produced 67 fewer false flags and 11 more misses.

| Model | Threshold | Misses / rejection | False flags / no rejection | Sensitivity (95% interval) | Specificity (95% interval) |
| --- | ---: | ---: | ---: | --- | --- |
| CatBoost | 0.876588 | 25 / 169 | 8 / 176 | 85.2% (79.7%–90.7%) | 95.5% (92.4%–98.3%) |
| Multivariable logistic | 0.853673 | 33 / 169 | 8 / 176 | 80.5% (74.3%–86.5%) | 95.5% (92.1%–98.2%) |
| IFNG | 0.520758 | 14 / 169 | 75 / 176 | 91.7% (87.1%–95.7%) | 57.4% (50.3%–64.5%) |
| Training constant | 0.500000 | 0 / 169 | 176 / 176 | 100.0% (100.0%–100.0%) | 0.0% (0.0%–0.0%) |

| Model | ROC-AUC (95% interval) | Average precision | Precision | Negative predictive value | Accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| CatBoost | 0.969 (0.952–0.983) | 0.972 | 94.7% | 87.0% | 90.4% |
| Multivariable logistic | 0.956 (0.935–0.974) | 0.958 | 94.4% | 83.6% | 88.1% |
| IFNG | 0.842 (0.799–0.884) | 0.794 | 67.4% | 87.8% | 74.2% |
| Training constant | 0.500 (0.500–0.500) | 0.490 | 49.0% | Undefined | 49.0% |

The constant score is the training rejection fraction, evaluated at 0.5. It flags every validation specimen because training prevalence exceeds 0.5. Its negative predictive value is undefined: it makes no negative predictions. The preserved original run used a zero-denominator fallback of zero; this analysis corrects that display without altering the run.

The selected threshold reached 90.2% sensitivity on screening data; validation sensitivity was 85.2%, below the experimental 90% target. Threshold selection and probability calibration are separate: a threshold picks a flagging rule; calibration asks whether scores correspond to observed fractions.

## Paired comparison and uncertainty

Intervals use 2,000 ordinary bootstrap resamples of 345 biopsy specimens with replacement, seed 20260915, and the 2.5th and 97.5th percentiles. Each resample uses the same specimen positions for every model. Models, preprocessing, and thresholds remain fixed. These intervals describe evaluation-sample uncertainty, not uncertainty from model fitting, feature selection, or threshold selection. Patient and center independence are unverified; repeated or related specimens could make these intervals too narrow. Small subgroup intervals are descriptive, with no multiplicity adjustment.

Differences below are **CatBoost minus the comparison model**. Negative miss/false-flag counts and Brier differences favor the selected model; positive sensitivity/specificity/AUC differences favor it. Count intervals describe differences in a same-size resampled cohort, not a forecast for a new clinic.

| Comparison | Metric | Difference | 95% paired interval |
| --- | --- | ---: | --- |
| Multivariable logistic | Sensitivity | +4.73 pp | -0.01 to +9.74 pp |
| Multivariable logistic | Specificity | +0.00 pp | -3.59 to +4.02 pp |
| Multivariable logistic | ROC-AUC | +0.0131 | +0.0001 to +0.0270 |
| Multivariable logistic | Brier score | -0.0075 | -0.0248 to +0.0099 |
| Multivariable logistic | Missed rejection | -8 | -17.00 to +0.02 |
| Multivariable logistic | False flags | +0 | -7.00 to +6.00 |
| IFNG | Sensitivity | -6.51 pp | -12.35 to -1.17 pp |
| IFNG | Specificity | +38.07 pp | +30.90 to +45.84 pp |
| IFNG | ROC-AUC | +0.1263 | +0.0866 to +0.1667 |
| IFNG | Brier score | -0.1068 | -0.1340 to -0.0790 |
| IFNG | Missed rejection | +11 | +2.00 to +21.00 |
| IFNG | False flags | -67 | -83.00 to -53.00 |

The point estimates favor CatBoost over logistic regression in this cohort, but the paired intervals show how much the comparison can vary. The ROC-AUC difference interval only just excludes zero under this fixed-model specimen-resampling calculation; its lower endpoint is about 0.0001. The sensitivity, miss-count, specificity, and Brier-difference intervals include zero. The practical advantage over logistic regression remains uncertain, and these intervals do not measure training or selection uncertainty.

## Missed rejection and false flags

These are errors against recorded histological labels, without chart review or adjudication. They do not establish which diagnosis is biologically correct.

| Original diagnosis | CatBoost errors / specimens | Logistic errors / specimens | IFNG errors / specimens | Error counted |
| --- | ---: | ---: | ---: | --- |
| No Rejection | 8 / 176 | 8 / 176 | 75 / 176 | False flag |
| Antibody-mediated Rejection | 6 / 56 | 8 / 56 | 9 / 56 | Missed rejection |
| T cell-mediated Rejection | 18 / 95 | 25 / 95 | 5 / 95 | Missed rejection |
| Mixed Rejection | 1 / 18 | 0 / 18 | 0 / 18 | Missed rejection |

The diagnosis plot and CSV show each denominator and 95% Wilson intervals. The subtype analysis evaluates the binary classifier; it is not a separate subtype-prediction task.

| Comparison with CatBoost | Error type | Both models wrong | CatBoost only wrong | Comparison only wrong |
| --- | --- | ---: | ---: | ---: |
| Multivariable logistic | missed rejection | 20 | 5 | 13 |
| Multivariable logistic | false flag | 2 | 6 | 6 |
| IFNG | missed rejection | 8 | 17 | 6 |
| IFNG | false flag | 5 | 3 | 70 |

The local specimen review is `data/processed/analysis/20260915_baseline/specimen_review.csv`; `selected_model_errors.csv` contains only the selected model's errors. They retain original diagnosis, assay date/cartridge/scanner, all model scores and decisions, and outcome categories. Per-specimen files are Git-ignored.

## Score reliability

The reliability plot uses ten fixed equal-width score bins: [0, 0.1), …, [0.9, 1]. Each point uses the actual mean score and observed rejection fraction within its bin. Counts and 95% Wilson intervals make sparse bins visible; empty bins have no point. Brier score is mean squared score error, so lower is better; it reflects both discrimination and calibration. A lower Brier score alone does not establish better calibration. Method reference: [scikit-learn probability calibration documentation](https://scikit-learn.org/stable/modules/calibration.html), accessed September 15, 2026.

| Model | Mean score | Observed rejection | Mean minus observed | Brier score (95% interval) |
| --- | ---: | ---: | ---: | --- |
| CatBoost | 52.7% | 49.0% | +3.7 pp | 0.078 (0.057–0.101) |
| Multivariable logistic | 51.8% | 49.0% | +2.9 pp | 0.086 (0.065–0.109) |
| IFNG | 63.6% | 49.0% | +14.6 pp | 0.185 (0.163–0.209) |
| Training constant | 66.1% | 49.0% | +17.1 pp | 0.279 (0.263–0.297) |

The selected model's average score differs from the observed fraction by +3.7 percentage points. Among its bins with at least 10 specimens, the largest score-versus-observation gap is in [0.8, 0.9): mean score 84.7%, but 7/16 (43.8%) had recorded rejection (95% Wilson interval 23.1%–66.8%). This is a descriptive example selected after inspecting the fixed bins. In the [0.9, 1.0] bin, mean score was 98.4% and 142/148 (95.9%) had rejection (95% Wilson interval 91.4%–98.1%). Good ranking does not by itself make each score a reliable probability, and agreement of averages does not establish calibration in each score range. Several bins contain few specimens. Continue calling the output a **model score**; no recalibration was fitted on validation data. Any future calibration fit must use discovery data and be evaluated as a separate follow-up analysis.

## Assay metadata and study composition

Metadata grouping uses deposited assay Date, CartridgeID, and ScannerID. These fields describe processing; they are not patient or center IDs and are excluded from model predictors. Every group table includes rejection and no-rejection denominators, original diagnosis counts, misses, false flags, and Wilson intervals for the two error rates.

| Split | Specimens | Rejection fraction | No rejection | Antibody-mediated | T cell-mediated | Mixed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 787 | 66.1% | 267 | 207 | 256 | 57 |
| discovery_screen | 263 | 66.2% | 89 | 69 | 86 | 19 |
| author_validation | 345 | 49.0% | 176 | 56 | 95 | 18 |

| Metadata field | Discovery groups | Validation groups | Groups shared across cohorts |
| --- | ---: | ---: | ---: |
| Date | 37 | 7 | 0 |
| CartridgeID | 96 | 31 | 0 |
| ScannerID | 1 | 1 | 1 |

| Validation scanner | Specimens | Rejection | Misses / rejection | False flags / no rejection |
| --- | ---: | ---: | ---: | ---: |
| 2010C0748 | 345 | 49.0% | 25 / 169 | 8 / 176 |

| Validation assay date | Specimens | Rejection fraction | Misses / rejection | False flags / no rejection |
| --- | ---: | ---: | ---: | ---: |
| 20211130 | 91 | 52.7% | 9 / 48 | 5 / 43 |
| 20211201 | 43 | 48.8% | 4 / 21 | 0 / 22 |
| 20211202 | 43 | 48.8% | 3 / 21 | 2 / 22 |
| 20211203 | 42 | 50.0% | 3 / 21 | 0 / 21 |
| 20211210 | 45 | 53.3% | 2 / 24 | 0 / 21 |
| 20211216 | 47 | 59.6% | 2 / 28 | 0 / 19 |
| 20211221 | 34 | 17.6% | 2 / 6 | 1 / 28 |

Discovery and validation used different dates and cartridges, but the same scanner. Those assay groups are therefore tied to cohort membership; they cannot separate cohort effects from assay effects. Assay-group error rates must be read alongside diagnosis composition and small denominators. The recorded groups do not isolate a scanner, cartridge, or date effect from specimen mix. These are descriptive checks, not evidence of a causal batch effect or verified transportability to new centers.

Viral assay-target interpretation is documented separately in [viral-target review](../20260915_viral/REPORT.md).

## Reproduce and inspect

```powershell
uv run python scripts/analyze_results.py --output-dir results/analysis/20260915_baseline_check --case-dir data/processed/analysis/20260915_baseline_check
```

This command reads saved predictions and cohort assignments, checks exact specimen sets and diagnosis mappings, verifies frozen flags and original aggregate results, then recomputes all summaries without fitting or changing thresholds. Saved inputs are verified against the completed-run manifest, and physical raw files against its public-source manifest. Inputs, hashes, settings, package versions, and output hashes are recorded in `analysis_manifest.json`. The original baseline outputs are preserved. Completed analysis and specimen-output directories are never overwritten; choose fresh directory names for each rerun. Additional reports may use `--run-dir`, `--output-dir`, and `--case-dir` with new project-relative directories.

### Main charts

Each PNG has an editable SVG with text retained as text and a corresponding aggregate CSV where applicable.

1. [ROC and precision–recall](figures/01_roc_precision_recall.svg)
2. [Confusion matrices](figures/02_confusion_matrices.svg)
3. [Absolute error counts](figures/03_absolute_errors.svg)
4. [Errors by diagnosis](figures/04_errors_by_diagnosis.svg)
5. [Score distributions](figures/05_score_distributions.svg)
6. [Score reliability](figures/06_score_reliability.svg)

Aggregate tables: `model_metrics.csv`, `metric_intervals.csv`, `paired_differences.csv`, `errors_by_diagnosis.csv`, `error_overlap.csv`, `reliability_bins.csv`, `assay_group_errors.csv`, and `cohort_composition.csv`. Full metric intervals include precision, negative predictive value, average precision, accuracy, Brier score, and error counts.

## Scope of the evidence

The data establish agreement with recorded rejection diagnoses in this deposited study. Technical validation is the authors' held-out cohort, not a prospective clinical trial. The study does not establish future rejection prediction, care benefit, clinical deployment, or patient/center independence. This analysis completes reporting of the existing fixed run; no new model, threshold, or calibrated model was selected from its validation results.
