# Presentation wording review, September 21, 2026

This note supports the user's requested revisions to slides 2, 3, 4, 10, 11,
and 12, including the clarity edits to slides 2–4. The accepted slide 7 bullets
and slide 9 script clarification are also incorporated. The 19-slide sequence,
planned 20-minute allocation, saved research,
and demonstrated model are unchanged.

## Borderline biopsies occur in practice

[Nankivell et al., 2019, *American Journal of Transplantation*](https://pubmed.ncbi.nlm.nih.gov/30501008/)
(19:1452–1463; DOI 10.1111/ajt.15197) compared 146 consecutive borderline
diagnoses with 826 normal controls and 55 acute T-cell-mediated rejection
diagnoses from 551 kidney transplant recipients at one center. The abstract
reports both resolution of borderline inflammation and subsequent acute
rejection. It also associates borderline findings with tubular injury, fibrosis,
and poorer graft outcomes. Outcomes differed between biopsies taken for impaired
function and scheduled protocol biopsies.

The study supports the Example box: "A biopsy shows mild inflammation, but not
enough to diagnose rejection. In a study of 146 borderline diagnoses, inflammation
disappeared in some patients. Others later developed acute rejection."
The 146 figure counts diagnoses, not unique people. It is not a general
prevalence estimate. The outcome percentages in the abstract refer to different
subsets and should not be presented as complementary outcomes for all 146 cases.
The example describes a clinical pattern rather than an invented patient.

The [current Banff reference guide](https://banfffoundation.org/central-repository-for-banff-classification-resources-3/)
(Banff-Kidney-2024-3, updated April 20, 2026) includes a diagnostic category for
findings suspicious or borderline for acute T-cell-mediated rejection. It also
addresses complex interpretations and thoroughly validated biopsy transcript
tests. This supports the proposed use of additional molecular evidence; it does
not establish this classifier's value in those cases.

## Why both errors matter

The wording that missed rejection can leave kidney injury untreated is a clinical
inference from rejection-associated injury and the role of diagnosis in treatment.
It is not an observed effect of this project's false negatives. Nankivell et al.
report injury and adverse outcomes associated with borderline findings.
[Wiebe et al., 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7496654/)
(DOI 10.1111/ajt.15860) also found lower graft survival among recipients with
borderline and definite T-cell-mediated rejection in a cohort of 803 recipients.
These observational associations do not measure the causal benefit of a model
detecting another case.

[KDIGO's 2009 guideline summary](https://kdigo.org/wp-content/uploads/2017/02/KITxpGL_summary.pdf),
recommendations 6.1–6.3, connects biopsy diagnosis to rejection treatment and
advises avoiding substantial treatment delay for biopsy. The
[2024 BK polyomavirus consensus](https://pmc.ncbi.nlm.nih.gov/articles/PMC11335089/),
Table 7 and the Management section, recommends reducing immune suppression for
sustained BK infection or BK nephropathy without concurrent rejection or high
immunologic risk. Together, these sources support the concern that unnecessary
rejection treatment can worsen an infection. The
[earlier biopsy-care review](BIOPSY_CARE_20260919.md) records further context.

The slide's limitation is: "This project has not established usefulness in
ambiguous biopsies. That requires comparing specialist assessment with and
without RNA scores."

## CatBoost rationale

The official [CatBoostClassifier reference](https://catboost.ai/docs/en/concepts/python-reference_catboostclassifier)
supports numerical predictors; categorical predictors are optional. The official
[parameter-tuning guide](https://catboost.ai/docs/en/concepts/parameter-tuning)
documents tree depth and other controls on model complexity. In this project,
the depth-four candidate provides a way to represent nonlinear patterns and
interactions among RNA measurements while limiting tree complexity. Shallow
trees are a control on overfitting, not a guarantee against it.

"Approach and rationale" accurately describes the slide's explanatory column.
The rationale does not depend on categorical predictors and does not claim
CatBoost is inherently more suitable than XGBoost or other alternatives. It
does not imply use of early stopping or other features absent from the saved run.

## Metric wording

Recall and precision share the true-positive numerator, "Correctly flagged
rejection cases." Their denominators differ: all cases diagnosed as rejection
for recall, and all rejection flags for precision. At a fixed true-positive
count, removing false positives reduces the precision denominator. It does not
turn false positives into true positives. The 90% recall requirement is the
project's screening selection rule; the validation recall remains below it.

The final CatBoost-versus-IFNG bullet is removed from slide 12, while the script
retains that comparison before explaining the constant baseline.
