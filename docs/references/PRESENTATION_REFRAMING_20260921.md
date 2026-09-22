# Comparative research question and model-choice explanation

Revision date: September 21, 2026. This is a documentation and presentation
revision on `codex/reframe-research-question`. It preserves the completed
analysis, model artifacts, thresholds and demonstration. No k-fold experiment
was run. Earlier source reviews and analysis reports retain their dated wording.

## Research question and potential use

How do the tested classifiers compare in distinguishing any recorded rejection
from no rejection in the public B-HOT biopsy dataset, particularly in missed
rejection and false positives?

The principal comparison is regularized multigene logistic regression versus
CatBoost. IFNG and a constant model provide supporting benchmarks. A possible
future use is a molecular score from an existing kidney-transplant biopsy that
a pathologist considers alongside histology and other clinical findings when
assessing rejection. This project evaluates candidate classifiers against
recorded diagnoses. Whether adding the score improves clinical diagnosis remains
untested. The proposed use is no longer restricted to ambiguous biopsies.

[Zhang et al.](https://pubmed.ncbi.nlm.nih.gov/38092179/), *Laboratory Investigation*
104 (2024), 100304, provides the direct precedent: regularized regression for four
recorded diagnoses using B-HOT measurements. The article and supplements were
reviewed locally on September 19, and the PubMed abstract was checked again on
September 21. This project's binary L2 logistic model does not reproduce the
published four-class LASSO. The [methodology review](../METHODOLOGY_REVIEW.md)
records the differences. No comparison of headline accuracies across these tasks
is made.

The clinical consequences of missed rejection and unnecessary rejection
treatment remain supported by the [biopsy-care review](BIOPSY_CARE_20260919.md).
Rosales's later-outcome findings and Nankivell's borderline diagnoses remain
background sources, but no longer organize the presentation's motivation.

## Screening selection, then validation and split stability

| Evidence | CatBoost | All-RNA logistic regression |
| --- | ---: | ---: |
| Screening rejection detected / 174 | 157 | 157 |
| Screening false positives / 89 | 5 | 6 |
| Validation missed rejection / 169 | 25 | 33 |
| Validation false positives / 176 | 8 | 8 |
| Selected in discovery-only follow-up / 20 repetitions | 13 | 7 |

The [saved screening results](../../results/reproduction/baseline/biopsy_screen.csv)
and [selection code](../../experiments/rejection_public/run.py) establish the
original reason for selection. Each threshold retained at least 90% screening
recall. The candidate comparison then maximized specificity, with ROC-AUC
breaking ties. One fewer false positive selected CatBoost over all-RNA logistic.
The chosen model and threshold stayed fixed for evaluation.

The [validation analysis](../../results/analysis/20260915_baseline/REPORT.md)
adds evidence favoring CatBoost: eight fewer missed rejection cases with the
same false-positive count. The paired sensitivity-difference interval includes
zero: +4.73 percentage points, with a specimen-bootstrap 95% interval of about
−0.01 to +9.74 percentage points. The interval conditions on the fitted models
and thresholds and does not include fitting or selection uncertainty.

The [stability follow-up](../../results/followup/20260917_stability/REPORT.md)
used 20 overlapping discovery splits, each with separate fitting, screening
and assessment partitions. CatBoost was selected 13 times and logistic seven.
These are selection counts, not the number of independent validation trials or
a probability that one model is best. Together with the validation uncertainty,
they leave a dependable preference between the two models unsettled.

Cross-validation within discovery is a proposed methodological next step.
[Next steps](../NEXT_STEPS.md) describes common folds, a bounded comparison and
separation of model/threshold selection from assessment. The original 787/263
split and all reported results remain the completed analysis.

## Presentation changes

| Slide | Change |
| --- | --- |
| 1 | Spoken comparative research question; title-only visual retained |
| 2 | Final spoken transition connects RNA with rejection assessment generally |
| 3 | Potential diagnostic use replaces the ambiguous-biopsy example |
| 4 | Zhang's classifier study and the project's binary comparison replace the previous Banff/Rosales emphasis; both error consequences remain |
| 10 | Spoken emphasis on logistic versus CatBoost, supported by simpler benchmarks |
| 11 | Editable screening table makes the five-versus-six selection explicit |
| 12 | Preserved validation chart, stronger explanation of the eight-case advantage and uncertainty, and the 13-to-seven stability result |
| 19 | Observed comparison and software, with cross-validation and clinical benefit identified as future work |

Visible slides 3, 4, 11, 12 and 19 change. Narration also changes on slides 1, 2
and 10. The 19-slide sequence, planned 20 minutes, separate HTML script and empty
PowerPoint notes remain. Current project guidance uses this framing. Dated
analysis reports and study audits are preserved as historical evidence.
