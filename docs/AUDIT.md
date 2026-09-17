# Defensibility and implementation audit

September 15, 2026 · Branch: `audit/defensibility-and-elegance`

This is the dated audit record. See [current status](STATUS.md) for later work:
the local container and a hosted CI run now have execution evidence. The
remaining-work list below describes the project on the audit date.

## Conclusion

The project is defensible as a retrospective research demonstration of agreement
with recorded biopsy diagnoses. The audit found no result-invalidating leakage,
label, split, or metric error in the reviewed workflow. It found several input
and reporting bugs, which are fixed on this branch.

The first pass established that the application had a small design, but did not
adequately address how its code reads. The second pass reorganized the training,
analysis, API, and browser workflows into named steps and expanded compressed
expressions. The application still uses one shared prediction package, one
FastAPI service, and one HTML page with plain JavaScript and CSS.

This review used the [saved UNOS job description](references/JOB_DESCRIPTION.txt).
It assesses the code and evidence available here; it is not an independent
clinical validation or a claim that every possible failure has been tested.

## Methodology

| Question | Finding |
| --- | --- |
| Are inputs and labels accounted for? | Both physical public inputs match their size and hash manifest. There are 1,395 specimens, 770 raw targets, and 758 predictors after removing housekeeping targets. Unknown diagnoses fail explicitly. |
| Is the split preserved? | The saved 787 training, 263 screening, and 345 technical-validation assignments match source diagnoses and author cohorts. There are no duplicate normalized profiles; this does not establish patient independence. |
| Can preprocessing leak across specimens? | Housekeeping normalization uses each specimen alone. Learned scaling and feature selection stay inside pipelines fitted on training rows. Diagnosis, identifiers, cohort, and assay metadata are excluded from predictors. |
| How were models chosen? | Nine configurations were fitted for each of three binary targets: 27 fits in total. Eight multivariable candidates compete within each target; IFNG is a separate benchmark. Model and threshold selection use discovery screening. |
| Is the comparison fair? | The constant, IFNG, full-panel logistic, and selected model use the same validation specimens. The fitted models and their screening-selected thresholds are retained. |
| Are the error claims proportionate? | The report gives denominators, missed rejection, false flags, and paired uncertainty. CatBoost's 85.2% validation sensitivity falls below the experimental 90% screening target. |
| Are scores calibrated probabilities? | No such claim is made. Reliability plots and Brier scores are reported, with sparse-bin uncertainty. The application returns a model score. |
| What does reproduction mean? | Reproduction of this project's fixed procedure. The source study's complete preprocessing and four-class LASSO classifier were not reconstructed. Subtype work is labeled follow-up analysis. |

The preprocessing review follows the distinction between fitting transforms on
training data and applying them to evaluation data in
[scikit-learn's leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html).
The score interpretation follows its
[calibration guidance](https://scikit-learn.org/stable/modules/calibration.html).
Both were checked on the audit date.

### Why retain CatBoost?

The saved discovery comparison is narrow:

| Model | Rejection detected / 174 | False flags / 89 |
| --- | ---: | ---: |
| CatBoost | 157 | 5 |
| Full-panel logistic regression | 157 | 6 |

CatBoost won the specified rule by one false flag. In technical validation it
missed eight fewer rejection cases, with the same number of false flags, but the
paired interval for the miss-count difference includes no difference.
[Screening table](../results/reproduction/baseline/biopsy_screen.csv) ·
[Validation and uncertainty](../results/analysis/20260915_baseline/REPORT.md)

Logistic regression remains a credible simpler alternative. The service retains
the frozen CatBoost model so this implementation audit preserves its demonstrated
behavior. This is a project choice, not evidence of established superiority.
A future model-choice comparison should specify how much improvement justifies
additional complexity using discovery data. The current validation cohort has
already been examined and cannot supply a new independent selection test.

### Assay quality and other limits

File checks do not establish laboratory assay quality. Raw RCC files contain
control probes and imaging/binding-density information, but this project has not
independently repeated those quality checks or used them to exclude specimens.
The API documentation now states that the laboratory must complete its assay
quality checks. The manufacturer describes these separately from normalization
in its [nCounter guidance](https://brukerspatialbiology.com/support/knowledgebase/ncounter-data-analysis/).

Patient and center independence remain unverified. Specimen-bootstrap intervals
hold models and thresholds fixed; they omit training and selection uncertainty
and may be too narrow if specimens are related. Study composition and assay
processing are partly confounded. These limits constrain generalization, rather
than invalidating a descriptive comparison within this dataset. An external
cohort would be needed for independent confirmation.

## Changes made

| Problem found | Smallest useful correction |
| --- | --- |
| Boolean values in mixed-type tables and complex counts could be silently converted to real counts. | Reject them before numeric conversion; add count-contract regression tests. |
| Repeated GEO metadata could replace a diagnosis or cohort assignment. | Reject duplicate fields and missing/duplicate specimen-accession rows before constructing the study table. |
| Analysis repeated the label mapping, hashing, and path rules; its path check allowed filesystem links. | Reuse the existing shared helpers and record their source hashes in new analysis manifests. Keep the dependency-free downloader verification available before package installation. |
| An existing empty subtype output directory passed validation and then failed during creation. | Reject existing destinations early and consistently in the reviewed analysis commands. |
| The viral report could state ranks and error conclusions from the original run when given another run. | Derive the narrative from that run's measured ranks, diagnoses, and error counts. Current aggregate tables are unchanged. |
| Malformed optional example descriptions could break the example-list endpoint. | Validate the small local manifest at startup; uploads remain available when examples are unusable. |
| The README mixed setup instructions with repeated development history. | Lead with the question, same-row error counts, demo command, and reproduction steps. Add a short code reading order; retain detailed evidence in its existing guides. |
| Some wording obscured the narrow model-selection margin and assay-QC scope. | State both directly and distinguish 27 total fits from 27 primary candidates. Clarify that hosted CI success still needs execution evidence. |

## Reading the revised implementation

The standard for this pass was whether a reader can follow the main operation,
understand each intermediate value, and find the corresponding calculation
without decoding abbreviations or hidden mutable settings.

| Entry point | What is now visible |
| --- | --- |
| [Training](../experiments/rejection_public/run.py) | `run_experiment` calls `prepare_data`, `fit_candidates`, and `freeze_and_evaluate`. Output directories are explicit arguments. Candidate order and configuration remain fixed. |
| [Normalization](../src/kidney_biopsy/preprocessing.py) | Validation, log counts, the housekeeping mean, subtraction, and ordered feature selection appear as separate steps. |
| [Model loading](../src/kidney_biopsy/prediction.py) | Paths, artifact checks, schema checks, and predictor construction have descriptive local names and a clear sequence. |
| [Analysis](../scripts/analyze_results.py) | A short CLI calls `analyze_run`; calculation, export, and manifest writing are distinct. Each of the six figures has its own named plotting function. |
| [HTTP prediction](../src/kidney_biopsy/api.py) | Request checks, CSV parsing, scoring, and response construction are visible in order. Optional local evidence loading follows the routes. |
| [Browser](../src/kidney_biopsy/static/app.js) | The request flow is separate from single-specimen and batch rendering. Event handlers and DOM construction use ordinary statements and descriptive names. |

The files use more lines because arguments and calculations are no longer packed
together. No new framework or generic abstraction was introduced. The report's
written content remains substantial, and historical runs retain their original
source snapshots. Those are different reading tasks from following a prediction.

## What remains worth keeping

- **One normalization and scoring path.** Training, CLI, and API share it.
- **Explicit input and artifact checks.** They prevent silent errors and loading
  incompatible models; removing them would compromise the application.
- **Research scripts.** They make fitting, threshold selection, and reports
  inspectable without a new orchestration framework.
- **Completed run snapshots.** They preserve how old results were produced. They
  are historical records, not competing copies of the live application.
- **Existing dependencies and frozen service model.** This audit adds no framework,
  dependency, endpoint, candidate model, or deployment platform.

## Initial verification

- [Before](../results/checks/20260915_audit/before.json): 55 passing tests.
- [Final checks](../results/checks/20260915_audit/final.json): 64 passing tests, including
  the newly identified failure cases, plus syntax and packaged-asset checks.
- [Real HTTP check](../results/checks/20260915_audit/http/http.json): all 345
  validation specimens agree with CLI and saved scores within `1.11e-16`; every
  flag agrees. Reordered columns, invalid batches, and upload limits were checked.
- [Report comparison](../results/checks/20260915_audit/report_comparison.json): all
  14 aggregate CSVs and the primary metrics JSON reproduce byte-for-byte. The new
  analysis manifest records the shared source hashes. All 35 subtype-run artifacts
  still match their preserved manifest.
- [Preserved runs](../results/checks/20260915_audit/preserved_runs.json): all 78
  recorded binary-run artifacts remain intact; the original and shared-code runs
  still agree across all nine evaluation tables.

The initial pass did not refit models. Its records are preserved above.

## Readability verification

- [64 existing tests pass](../results/checks/20260915_readability/checks.json).
  No tests were added solely to mirror the refactoring.
- [Full training reproduction](../results/checks/20260915_readability/reproduction.json):
  all 27 fits were rerun in a new directory. All nine evaluation tables, selected
  models, thresholds, and split assignments match the original; score differences
  are exactly zero.
- [Real HTTP comparison](../results/checks/20260915_readability/http/http.json):
  all 345 specimens agree with CLI and saved predictions within `1.11e-16`, with
  identical flags.
- [Browser checks](../results/checks/20260915_readability/browser.json): valid and
  invalid examples, a two-specimen upload, clearing stale results, rejection of a
  changed server model, and recovery after reloading all work.
- [Report comparison](../results/checks/20260915_readability/analysis_comparison.json):
  all eight real-data aggregate tables, the metrics JSON, and all six PNG charts
  reproduce the preserved analysis byte-for-byte.

The reproduction is saved under `results/reproduction/20260915_readability` with
its own source snapshots and model artifacts. Completed runs were not overwritten.

## Fit to the role and remaining work

The strongest evidence for the role is a reproducible analysis connected to
validated software: data preparation, model comparison, a shared prediction
path, an API, meaningful tests, and a small usable demonstration.

The remaining deliverables are an editable 20-minute presentation, timed
rehearsals, and actual local container execution. The CI workflow exists, but a
hosted passing run must be verified separately. A small cloud deployment remains
a target if access permits. This dataset does not demonstrate terabyte-scale
work, and a solo project does not establish experience on a production team.

The next useful step is to explain this existing work clearly and complete the
remaining delivery checks. Additional tuning, infrastructure, or frameworks are
not required to make the current research demonstration defensible.
