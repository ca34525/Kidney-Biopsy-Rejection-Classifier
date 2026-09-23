# Deferred work

Presentation delivery takes priority; its remaining tasks are in the
[presentation README](../presentation/README.md#rehearsal-and-backup).
The items below do not change the frozen model or current implementation scope.

## Research priorities

1. **Compare logistic regression and CatBoost using common discovery folds.**
   Use nested selection: fit preprocessing, tune settings and choose thresholds
   inside each outer training partition, then assess the retained model on its
   held-out fold. Specify what improvement would justify greater complexity and
   how a final fitted model receives a compatible threshold. The completed
   [20-split follow-up](../results/followup/20260917_stability/REPORT.md) is
   overlapping split analysis, not k-fold cross-validation. Methods:
   [nested cross-validation](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html)
   and [threshold selection](https://scikit-learn.org/stable/modules/classification_threshold.html),
   reviewed September 21, 2026.
2. **Test whether the score adds useful evidence during rejection assessment.**
   Compare usual assessment with assessment that includes the score, using
   independent expert review or relevant outcomes. Measure improved and worsened
   assessments, assay failures, time and cost. Agreement with training labels
   alone does not answer this question. [Clinical context](RESEARCH_CONTEXT.md).
3. **Evaluate a new assay-compatible cohort.** Establish patient and center
   identities, inclusion rules and laboratory quality before inspecting results.
   No suitable external cohort has been established here. Obtaining the current
   study's specimen-level native-kidney mapping would also permit a transplant-only
   assessment. [Population limits](references/STUDY_AUDIT_20260919.md).

The existing technical-validation cohort has already been examined. Changes
informed by it are follow-up analysis; rerunning the fixed procedure is reproduction.
Preserve completed runs and give new experiments separate configurations and outputs.

## Supporting questions

| Question | Necessary preparation |
| --- | --- |
| Assay quality, batch effects and viral targets | Review manufacturer QC guidance; check whether batch-separated evaluation is feasible; predeclare viral-target removal comparisons. The [viral review](../results/analysis/20260915_viral/REPORT.md) supplies associations, not causal explanations. |
| Score calibration | Fit calibration using discovery data separated from model fitting, then assess reliability and errors. Threshold selection is a different task. See [current reliability results](../results/analysis/20260915_baseline/REPORT.md#score-reliability) and [calibration guidance](https://scikit-learn.org/stable/modules/calibration.html). |
| Reconstruct Zhang's model | Match the published four-class endpoint, preprocessing, feature selection and fitting procedure; the existing subtype follow-up is not that reconstruction. |
| Predict later rejection | Find measurements taken before a defined future outcome, with adequate follow-up. The current biopsy diagnosis cannot establish future prediction. |
| Cloud demonstration | Follow the [AWS procedure](AWS_DEPLOYMENT.md) when account access and time permit; record real endpoint checks and cleanup. |

Threshold exploration, individual feature explanations, larger searches, and
capacity/recovery exercises can wait until a specific question warrants them.
Recheck external methods and service documentation before implementing deferred work.
