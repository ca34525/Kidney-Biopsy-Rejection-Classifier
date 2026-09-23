# Methodology compared with the source study

Reviewed September 21, 2026, against the supplied article, its Supplementary
Methods, the current training and preprocessing code, and preserved project
results. This is an assessment of the existing procedure. It does not introduce
a new experiment or change a fitted model, threshold, or completed run.

## Judgment

The method is defensible for a retrospective comparison of models that classify
recorded rejection diagnoses in the deposited biopsy cohort. Its useful evidence
is the same-specimen comparison, explicit error counts, reproducible processing,
and a tested prediction path. Agreement with those diagnoses is an early step
toward the proposed molecular second opinion; this study has not tested whether
that score helps specialists interpret uncertain biopsies.

The paper does not require every subsequent analysis to use its classifier.
Different choices need a clear question, consistent evaluation, and an account
of what the comparison cannot establish. Our largest weaknesses are the original
model-selection design and limited evidence of transfer to other specimen and
assay populations. The current results do not establish that CatBoost is the
best model family or that this project improves on the published classifier.

## What differs, and whether it is reasonable

| Choice | Source study | This project and assessment |
| --- | --- | --- |
| Outcome | Four molecular classes corresponding to recorded No Rejection, ABMR, TCMR, and Mixed Rejection diagnoses; highest class score supplies the call (p. 3). | Any recorded rejection versus no rejection is a coherent, narrower question. It loses subtype information; a binary score cannot identify the appropriate treatment. Four-class and binary accuracy are not directly comparable. The separate subtype extension remains follow-up analysis. |
| Normalization | Housekeeping normalization against the pooled 1,050-specimen discovery reference, with the manufacturer's processing procedure and ComBat-seq for two assay lots (p. 3). | The shared transform uses each specimen's 12 housekeeping measurements and learns nothing from other specimens. This is an explicit, reproducible alternative for the research comparison. Equivalence to the authors' full processing, or superiority over it, has not been tested. |
| Assay quality | Excluded 35 discovery and five validation specimens using laboratory QC rules (pp. 3-4). | The deposited 1,395 specimens are the source study's retained set. Our file and number checks do not independently repeat laboratory QC; scoring further specimens requires compatible measurements and completed laboratory quality checks. |
| Features | Removed 13 targets annotated as specific to other organs; fitted from 745 candidates, with 143 receiving nonzero weights (pp. 3, 5). | Retains all 758 non-housekeeping targets. This is a transparent fixed feature set, with selection and scaling fitted only on training rows where used. Extra targets can add noise or study-specific associations; keeping them has not been shown to help. A 745-target sensitivity comparison would address this directly. |
| Regression comparator | Multiclass L1-regularized regression (LASSO), selected for similar accuracy with fewer weighted genes; repeated ten-fold cross-validation for model-family comparisons (p. 3; Supplementary Methods). | The original full-panel comparator is binary L2-regularized logistic regression with fixed C = 0.1. It is a meaningful simpler comparator, but it is not a reproduction of the published LASSO model or a thoroughly tuned regression benchmark. |
| Selection and threshold | Compared model families on common repeated folds; the final multiclass call uses the highest score. | Fits on 787 discovery specimens, then selects thresholds and a model on 263 screening specimens. The code saves that choice before scoring 345 author-validation specimens. This separates selection from evaluation, but one screening split is sensitive to which specimens it contains. |
| Error preference | Multiclass classification, with particular concern about false rejection calls in infection controls (p. 13). | Requiring at least 90% screening recall, then minimizing false flags, is a stated research preference. It is not a clinical cost model or a guarantee: validation recall was 144/169, or 85.2%. Threshold selection does not calibrate probabilities. |
| Evaluation population | Selected retrospective biopsies, including native-kidney controls; all processed at Arkana Laboratories. Patient and referring-center separation is not documented. | Preserving the author cohorts enables an understandable comparison on the source population. It does not establish performance in a transplant-only cohort, at a new laboratory, or on independent patients and referring centers. |

## Normalization and batch correction need separate explanations

The implemented feature is

```text
log2(target count + 1) - mean(log2(housekeeping count + 1))
```

This is the log of a target-to-reference ratio, using the geometric mean of the
12 housekeeping counts after adding one. It adjusts for specimen-wide scale
differences under the assumption that those references are suitable. Adding one
makes zero counts usable, but also affects low-count measurements. Neither that
choice nor reference stability has been independently validated here.

For a simple multiplicative housekeeping correction, scaling every specimen to
one fixed pooled reference adds a common constant after taking logs. The absence
of that constant alone is not a reason to reject our transform. This observation
does not make the full pipelines equivalent: processing steps, the handling of
low counts, assay QC, and batch correction also matter. Any learned reference or
batch transform in a future comparison should be fitted within the development
training partitions and have a defined procedure for scoring new specimens.

The paper reports that removing ComBat-seq changed fewer than 4% of validation
molecular class calls and left overall accuracy almost identical (p. 14). That
tempers concern that omitting it necessarily invalidates classification on this
dataset. It does not establish batch robustness for our models, normalization,
or future assay lots. The project's existing assay-group error tables are
descriptive; they do not isolate batch effects from differences in specimens.

## The model-choice claim should remain modest

The original search included four CatBoost configurations and two logistic
configurations, with only one logistic regularization strength. Common rows,
preprocessing, and a threshold rule make the observed comparisons interpretable,
but the search was not balanced enough to establish which model family is best.
Screening performance is also optimistic as a performance estimate because
screening chooses both thresholds and the winning candidate.

CatBoost detected 157 of 174 screening rejection specimens with five false flags;
full-panel logistic detected the same 157 with six false flags. That one-case
margin selected CatBoost under the fixed rule. On author validation, CatBoost
missed 25 rejection specimens and logistic missed 33; both made eight false
flags. The paired interval for their recall difference includes zero. Those
results support reporting the observed difference, not established superiority.

The discovery-only stability follow-up gives the comparison useful additional
context: it considered three logistic regularization strengths and two CatBoost
depths, selecting CatBoost in 13 of 20 repetitions and logistic in seven. Each
repetition had separate fitting, screening, and assessment specimens. Those
overlapping repetitions show variation with the split; they are not independent
validation trials or the paper's repeated cross-validation procedure.

Keeping the frozen CatBoost artifact preserves the demonstrated procedure. For
a new model-selection study, I would give regularized logistic regression first
consideration, tune it and CatBoost on common discovery partitions, and specify
what improvement would justify the additional complexity. A change prompted by
the already-seen evaluation remains follow-up analysis; a new cohort is needed
for independent confirmation.

## Population and interpretation remain the larger limits

The discovery No Rejection group contains 191 native-kidney controls among 356
specimens; validation contains 11 among 176. This change in composition can
affect how well a model transfers. The public metadata lack the individual
native-kidney identifiers, so we cannot compute transplant-only performance or
attribute errors to those controls from the available rows.

The paper deliberately included inflammatory infection controls. Viral assay
targets can therefore carry relevant information for the recorded label, but
their usefulness may depend on that study composition. The project's BK-target
review describes associations; it does not establish rejection-specific biology
or prove that removing those targets would improve transfer. IFNG likewise has
a biological rationale as a simple benchmark, but was not established as the
best single marker or as specific to rejection.

Several uncertain diagnostic categories were excluded by the source study.
The model has learned agreement with curated diagnoses, not an independent
resolution of disputed disease states. Specimen-level bootstrap intervals also
omit fitting and selection uncertainty and cannot account for unknown repeated
patients. These limits belong beside claims about future use.

The most useful further research would obtain specimen-level native/allograft
and patient/center information, assess laboratory QC and processing sensitivity,
and evaluate a frozen procedure in another compatible cohort. These are ways to
strengthen the next study; they do not prevent presenting this completed
classification and software project with its stated scope.

## Evidence

- [Source-study audit with page references](references/STUDY_AUDIT_20260919.md) and [article/supplement provenance](references/rejection_source_manifest.json). Article: Zhang et al., *Laboratory Investigation* 104 (2024), 100304, [DOI](https://doi.org/10.1016/j.labinv.2023.100304). Model-family comparisons are in Supplementary Methods, Diagnostic Model Fitting.
- [Actual training and selection](../experiments/rejection_public/run.py), [shared normalization](../src/kidney_biopsy/preprocessing.py), and [original screening results](../results/reproduction/baseline/biopsy_screen.csv).
- [Fixed validation analysis](../results/analysis/20260915_baseline/REPORT.md), [discovery-only stability](../results/followup/20260917_stability/REPORT.md), [subtype follow-up](../results/followup/20260915_subtypes/REPORT.md), and [viral-target review](../results/analysis/20260915_viral/REPORT.md).

The September 21 documentation corrections date the review statement, carry the
source-population qualification into the demo and future reports, and correct
the current talk count to 20 main slides. The script now identifies the constant
baseline's fixed 0.5 threshold, and the model-settings backup identifies C = 0.1
as the all-RNA logistic setting. Preserved reports and numerical runs remain
records of their original dates.

### CatBoost rationale

The September 21 source review checked the official
[CatBoostClassifier reference](https://catboost.ai/docs/en/concepts/python-reference_catboostclassifier)
and [parameter-tuning guide](https://catboost.ai/docs/en/concepts/parameter-tuning).
Numerical predictors are supported without categorical inputs. Shallow trees
limit complexity while allowing nonlinear patterns and interactions; this does
not establish superiority over other boosting libraries or guarantee against
overfitting. Do not imply early stopping was used in the saved recipe.
