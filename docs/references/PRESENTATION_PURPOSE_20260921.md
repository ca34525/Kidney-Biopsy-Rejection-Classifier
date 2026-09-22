# Established application and project purpose

Final purpose revision: September 21, 2026, on
`codex/reframe-research-question`. This updates the clinical framing in the
[earlier same-day revision](PRESENTATION_REFRAMING_20260921.md). That record's
screening, validation and stability evidence remains unchanged.

## Approved explanation

Molecular measurements already have a recognized role in parts of transplant
rejection assessment. I used this established application to investigate a
practical modeling choice: how much does the classifier change the rejection
cases missed and the false flags produced? The purpose was to assess what a more
complex model contributes before pursuing further validation, and to build
scoring software that preserves the evaluated procedure.

The purpose is the reason to make the comparison. The research question specifies
how to examine it using the public data. The contribution is an independent
applied comparison and tested scoring software. It does not require a claim that
molecular usefulness is newly discovered or that prior studies omitted algorithm
comparisons.

## Source support and scope

The [Banff Current Reference Guide](https://banfffoundation.org/central-repository-for-banff-classification-resources-3/),
version Banff-Kidney-2024-3, updated April 20, 2026, was checked again on September
21, 2026. Its additional diagnostic parameters, antibody-mediated rejection
criteria and AMR/MVI framework include biopsy transcript diagnostics that meet a
defined threshold and have been thoroughly validated for the specified use.
This establishes a recognized role for molecular evidence in defined settings.
It does not establish that every molecular score, rejection category or proposed
use has that validation. In the presentation, the concise wording is that
validated biopsy transcript tests have a defined role in antibody-mediated
rejection assessment.

[Zhang et al.](https://pubmed.ncbi.nlm.nih.gov/38092179/), *Laboratory Investigation*
104 (2024), 100304, supplies the public data and the direct research precedent.
The [Supplementary Methods](https://ars.els-cdn.com/content/image/1-s2.0-S0023683723002477-mmc6.docx)
compare regularized regression, random forests, gradient boosting, nearest
neighbors and support vector machines. With similar accuracy, the authors chose
LASSO for fewer weighted features. The full article and supplements were reviewed
locally on September 19. This makes regularized multigene regression an important
comparator; it also prevents claiming that comparing model families is a new gap.
Our binary L2 logistic model is not a reconstruction of their four-class LASSO.

The project's data show errors relative to recorded diagnoses. CatBoost's
validation result supports taking it seriously as a candidate, while the paired
uncertainty and discovery split results leave a dependable preference unsettled.
The recognized molecular application gives that modeling decision a relevant
context. Added diagnostic value from this particular score would need direct
evaluation. This distinction concerns the project's evidence, not doubt about
whether molecular tests can have a role in general.

Both error consequences retain the evidence in the
[biopsy-care source review](BIOPSY_CARE_20260919.md). The earlier framing record
retains the exact model-selection counts and their sources.

## Presentation changes in this round

| Slide | Change |
| --- | --- |
| 1 | Spoken opening connects the established application to the classifier choice |
| 2 | Spoken transition introduces the recognized role of molecular evidence |
| 3 | Purpose: assess the contribution of a more complex classifier before further validation and preserve the procedure in software |
| 4 | Banff restored, Zhang's previous algorithm comparison and simpler-model choice made explicit, both error consequences retained |
| 19 | Conclusion returns to evidence for the classifier choice and software that preserves the calculation |

Visible slides 3, 4 and 19 and narration on 1, 2, 3, 4 and 19 change in this round.
The screening counts, validation chart and split-stability explanation remain.
All slide timings, the 19-slide sequence, empty PowerPoint notes and separate HTML
script remain. Active project guidance now uses this purpose. Dated analyses and
earlier source reviews retain their historical wording. No experiments, model
artifacts, thresholds, prediction software or completed results change.
