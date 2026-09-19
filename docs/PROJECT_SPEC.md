# Kidney biopsy rejection classifier project specification

Specification date: September 15, 2026; clinical rationale updated September 18,
2026; source-population clarification September 19, 2026. Planning horizon: one week. Presentation:
20 full minutes, with questions outside that time. The exact interview date has
not been supplied.

## Objective

Develop an early research prototype toward a **molecular second opinion for
uncertain kidney transplant biopsies**. RNA measurements could add evidence when
microscopic findings are borderline, incomplete, or inconsistent with other
clinical information. The aim is to get more useful information from tissue
already collected. The dated clinical sources and related UNOS research are
recorded in [Research context](RESEARCH_CONTEXT.md#why-a-molecular-second-opinion-could-be-useful).

The analysis objective is to build a reproducible classifier that uses molecular
measurements from an already collected kidney biopsy to predict its
recorded rejection diagnosis. Package it as a small, tested application and explain
the work in a 20-minute interview presentation.

The intended research user is a transplant pathology or molecular laboratory team
developing an additional assessment for difficult biopsies. This project's current
contribution is to test agreement with recorded diagnoses and make the scoring
procedure reproducible. A useful demonstration shows an assay-compatible specimen,
its model score, the chosen threshold, and the kinds of errors observed in
evaluation. Added benefit in uncertain cases would require a separate comparison
of standard assessment with and without molecular information.

The role emphasizes developing data products and taking analytical prototypes
toward maintainable software. Success therefore means a credible analysis, working
software, and a clear account of decisions. It does not depend on a particular
accuracy score or a new scientific discovery. The detailed mapping is in
[Job requirements](JOB_REQUIREMENTS.md).

## Scope and deliverables

| Priority | Deliverable | Completion standard |
| --- | --- | --- |
| Required | Independent project | Code, raw inputs, environment, and generated outputs live here; no dependency on another project |
| Required | Reproducible analysis | A documented command downloads or verifies inputs, and a second command trains and evaluates models |
| Required | Model comparison | Constant, IFNG, regularized logistic, and CatBoost results use the same evaluation rows |
| Required | Research prediction service | Validated input produces a versioned score and flag through a documented API |
| Required | Small demonstration | A simple page shows a valid example and explains an invalid input without a traceback |
| Required | Software checks | Meaningful tests, one CI workflow, a local container run, and an understandable setup guide |
| Required | Interview package | Editable slides, PDF backup, separate HTML speaking script, source references, and a rehearsed 20-minute delivery |
| Target if access permits | Cloud demonstration | One small deployment to AWS, Azure, or Google Cloud, with actual run evidence and cleanup instructions |
| Optional | Further research | External cohort, published-model reconstruction, or a justified sensitivity analysis after the core works |

The cloud demonstration addresses an explicit skill in the posting. If account
access or time prevents it, record the gap and deliver the local application.
A deployment diagram alone is not evidence of cloud experience. There is no need
for a paid service, a public clinical endpoint, or a production platform.

## Data and prediction contract

Use public [GSE212160](https://ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212160):
1,395 kidney-biopsy specimens measured on the NanoString B-HOT panel: 1,193
transplant biopsies and 202 native-kidney controls. The controls include diseased
native kidneys. The source describes 770 measurements, including 12 housekeeping
targets and 758 assay targets.
These tissue-level RNA measurements reflect both activity within cells and the
mixture of cell types in the specimen.

The discovery cohort contains 859 transplant and 191 native-kidney specimens;
technical validation contains 334 transplant and 11 native-kidney specimens.
The public metadata do not map native-kidney status to individual specimens, so
the existing results describe the combined population. The
[September 19 source review](references/STUDY_AUDIT_20260919.md) records these
counts from the full study. Completed runs retain their original inputs and outputs.

**Unit of observation:** one biopsy specimen. **Prediction time:** after biopsy
tissue has been collected and the compatible molecular assay is available.
**Primary label:** recorded histological rejection in that specimen.

| Original diagnosis | Binary target |
| --- | ---: |
| No Rejection | 0 |
| Antibody-mediated Rejection | 1 |
| T cell-mediated Rejection | 1 |
| Mixed Rejection | 1 |

Preserve the source metadata field spelling in the parser and expose a correctly
named field internally. Unknown or missing labels must produce an explicit error
or an exclusion with a recorded reason.

Store original downloads under `data/raw/`. Keep processed tables, models, and
source-document copies under ignored local data directories. Track the small
public-source manifest with accession, URL, retrieval date, size, and SHA-256 hash.
Keep sample joins explicit and account for all included and excluded specimens.

Normalize raw counts within each specimen:

```text
normalized target = log2(raw count + 1)
                    - mean(log2(housekeeping counts + 1))
```

Use the 12 named housekeeping targets, then remove them from the predictor set.
Maintain the exact ordered feature names in the model metadata. Some panel targets
measure viral signals, so describe the inputs as assay targets when precision matters.
The deposited processed expression matrix may supply metadata but must not silently
replace the specified raw-count preprocessing.

The input contract must detect missing or duplicate targets, empty files, duplicate
specimen IDs, nonnumeric values, negative counts, and non-finite values. Accept
reordered valid columns by matching names. Treat extra columns by a documented
policy rather than accidentally using them as predictors. Numeric validation
cannot establish that an arbitrary file came from the correct assay; state that
assay compatibility is a caller requirement.

## Evaluation and model selection

Preserve the authors' 1,050-specimen discovery cohort and 345-specimen technical
validation cohort. Split discovery into 787 training and 263 screening specimens,
stratified by the original four diagnoses, with seed `20260915`. Save the actual
assignments. Check joins, cross-split duplicate records, and class counts.
All biopsies were processed at Arkana Laboratories. The study does not document
unique recipient counts, repeated biopsies, or patient and referring-center
separation between cohorts; specimen-level splitting does not establish those properties.

Train the baseline models and a bounded set of candidates. The starting recipe
includes CatBoost with 300 trees, depths 4 and 6, learning rate 0.04, and seed 2026;
full-panel and selected-feature regularized logistic models; and a few existing
tree-model alternatives. Keep the binary classifier as the benchmark for the
subtype follow-up below.

Use screening data to set a threshold for each model: maximize specificity while
retaining at least 90% of screening rejection cases. Choose the main model using
that operating result, with ROC-AUC as a tie-breaker. Preserve the fitted model
used to choose its threshold. Refitting requires a compatible threshold-selection
procedure, rather than transferring an old threshold without checking it.

This sensitivity target is an experiment choice, not a clinical requirement or
a guaranteed evaluation result. Report any shortfall in straightforward terms.

Evaluate the selected model, the IFNG model, a full-panel regularized logistic
baseline, and a training-derived constant baseline on the same rows. Freeze the
logistic configuration using discovery data before evaluating it. The comparison
should show whether the more complicated model improves results enough to justify
its use.

Report:

- Sample and class counts, confusion matrix, sensitivity, specificity, precision,
  and negative predictive value at each stated threshold.
- ROC-AUC and average precision, naming the metric precisely. Include prevalence
  with the precision-recall plot.
- Accuracy as supporting context, plus absolute differences in false flags and
  missed rejection cases between models.
- Simple uncertainty intervals for the central results. Explain the resampling
  unit and avoid implying verified patient independence when IDs are unavailable.
- A compact error review by original rejection subtype and available assay metadata.
  Review important viral targets and whether study composition could explain their
  contribution. Do not turn feature importance into a causal claim.

Assess score calibration with a reliability plot and Brier score before describing
scores as reliable probabilities. Post-hoc calibration, if useful, must use discovery
data. Do not make calibration a prerequisite for presenting a clearly labeled score.

**Reproduction note:** rerunning the same fixed procedure is reproduction. If
evaluation results lead to changes, describe the new comparison as follow-up work.
Keep this distinction in the methods; it does not block ordinary development.

### Rejection subtype follow-up

Compare four-class CatBoost with multinomial logistic regression using the same
split and shared preprocessing. Predict the four recorded diagnoses above, and
compare with the separate antibody-mediated and T-cell-mediated component models;
mixed rejection is positive for both components. Limit this extension to these
existing labels.

- Choose configurations and any thresholds using discovery data. Score every
  specimen directly; do not require a positive binary flag before assessing subtype.
- Report a four-by-four confusion matrix, class counts, and sensitivity and
  precision for each class, with particular attention to mixed rejection. Use the
  highest class score for the four-class prediction.
- Sum the three rejection-class scores to obtain an any-rejection score. Select
  its threshold using the existing discovery-screen sensitivity rule and compare
  missed rejection and false flags with the binary benchmark on the same rows.
- Compare component-model errors, including recognition of mixed rejection, to
  assess whether separate component scores describe the recorded diagnoses better.

The technical-validation cohort has already been examined, so label this extension
as follow-up analysis. Independent confirmation would require a new cohort.

## Software design

Use Python 3.12 with `uv`. Start from the working research scripts, then extract
shared parsing, validation, preprocessing, and prediction into `src/kidney_biopsy/`.
Keep a small command-line interface for training, evaluation, and batch prediction.
Choose FastAPI for the service and a simple HTML page served alongside it for the
demonstration. A separate frontend build system is unnecessary for the core task.

The proposed service contract is:

| Route | Behavior |
| --- | --- |
| `GET /health` | Reports service readiness and whether the configured model loaded |
| `GET /model` | Returns target, model version, assay/schema version, required targets, and threshold |
| `POST /predict` | Accepts a small CSV batch of raw assay counts and returns one result per valid specimen |

Each successful prediction includes specimen ID, `rejection_score`,
`rejection_flag`, threshold, model version, and concise input-check information.
The flag means the score crossed a research threshold. Invalid requests return
a structured explanation. Do not silently fill missing assay targets or return
predictions for invalid specimens. Use an all-or-nothing batch policy initially.

Set a small documented batch and upload-size limit. Load only the configured local
model, never an uploaded model file. Do not retain request bodies or raw uploaded
counts in logs. The application does not need user accounts for a local demo.

The page needs only a sample selector or file upload, the result, and a short
explanation of the threshold and observed errors. Keep analysis plots available
for the presenter. Use the default frozen threshold in the main demonstration;
any exploratory threshold view must be clearly labeled.

## Reproducibility and checks

Record input hashes, split, package versions, configuration, elapsed time, model
metadata, and evaluation output for each completed run. Write new runs to their
own directories. Store aggregate scores and reports in Git; keep raw data, per-specimen tables,
model binaries, local environments, caches, and secrets ignored.

Required checks must demonstrate:

1. The source manifest matches the physical files in this folder.
2. All sample joins and label mappings are accounted for.
3. Training and prediction apply the same transformation.
4. Reordering input columns preserves a prediction and malformed inputs fail clearly.
5. Saving and reloading a model preserves scores within a documented numeric tolerance.
6. The API and command-line route agree for the same specimen.
7. The local container starts and completes a valid request.
8. A fresh environment follows the documented setup without another project folder.

Use one CI workflow for fast tests and basic code checks. Keep the full training
run separate if its cost would slow routine development. Report measured runtime
and data size; do not describe this dataset as terabyte-scale work.

## Presentation acceptance

Deliver the files and timing specified in [Presentation specification](PRESENTATION_SPEC.md).
Every displayed result must come from an identified run in this folder. The
candidate should be able to explain the target, reproduce a prediction, justify
the comparison, and describe the parts built with AI assistance. Do not invent
teamwork, cloud work, or personal experience to match the posting.

## Boundaries

This is a study of recorded diagnoses using an existing assay panel. It is not a
biopsy-image model, a blood test, a future rejection forecast, or an organ-allocation
tool. Patient benefit and care decisions would need separate evidence. A short
explanation of those limits belongs in the talk; most presentation time belongs
to the actual question, results, software, and decisions.
