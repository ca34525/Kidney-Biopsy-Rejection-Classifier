# Research context

Public-source context first captured on 2026-09-15; clinical rationale updated
2026-09-18; full source study reviewed on 2026-09-19; comparative framing updated
2026-09-21; practical-purpose framing updated 2026-09-22. This document defines the research question and its motivation. Model
findings must come from runs performed in this project.

## Established application and project purpose

Whether a transplanted kidney shows rejection can affect decisions about further
treatment to suppress the immune system. That gives rejection detection a
practical reason even when a binary result does not specify the rejection subtype
or select a treatment. A molecular score could provide additional evidence during
this assessment, alongside histology and other clinical findings. This is the
potential use motivating the project.

The clinical connection is concrete: Zhang's Discussion (page 13) emphasizes
whether a biopsy diagnosis prompts further immunosuppression and explains the
inclusion of infection controls. [KDIGO's transplant-recipient guideline](https://kdigo.org/wp-content/uploads/2017/02/KITxpGL_summary.pdf),
recommendations 6.1–6.4, links biopsy assessment to rejection treatment and
distinguishes treatment for different rejection types. A binary score could
inform part of that assessment; the type, activity and other findings remain
important for care. The proposed role for **this score** is an inference from
that clinical context, not an observed benefit in the current experiment.

The project has two equally prominent aims:

- **Model comparison:** How do logistic regression and CatBoost compare in
  classifying any recorded rejection versus no rejection from B-HOT biopsy RNA,
  particularly in missed cases and incorrect flags? IFNG and a constant model
  supply supporting benchmarks.
- **Software engineering:** Make preprocessing, training and evaluation
  reproducible. Build a tested scoring service and prototype application that
  let a user submit a specimen's RNA counts and inspect its model score,
  threshold and rejection flag.

The prototype gives an analyst or molecular laboratory researcher a way to try
the selected model on compatible input, inspect its output, and integrate the
same scoring procedure into other software. This is a useful research
demonstration while the potential clinical role remains open for investigation.

The completed analysis measures agreement with recorded diagnoses. A comparison
of assessment with and without the score would address added diagnostic value.
That is a next research question, rather than a prerequisite for motivating an
applied analysis and software project. Molecular measurements already have a
recognized role in defined Banff settings, which supplies related clinical context.

Training for the binary endpoint is a substantive difference from Zhang's
four-class study. It does not establish that a binary approach is clinically
preferable: a four-class model can also supply an overall rejection flag. The
project's binary accuracy and the paper's four-class accuracy measure different
tasks and must not be presented as evidence of outperforming Zhang.

### Evidence supporting the application

Zhang's study is the direct classification precedent and was reviewed in full on
**2026-09-19**. The related clinical and UNOS sources were checked on
**2026-09-18**; they provide background rather than the endpoint for this project.
The current Banff reference was checked again on **2026-09-21**.

| Source and date | What it supports | Scope of the evidence |
| --- | --- | --- |
| Zhang et al., [Development and Validation of a Multiclass Model Defining Molecular Archetypes of Kidney Transplant Rejection](https://pubmed.ncbi.nlm.nih.gov/38092179/), *Laboratory Investigation*, 2024 | Uses B-HOT measurements and regularized regression to classify four recorded diagnoses. Provides the public data and a reason to include regularized multigene regression. | This project compares binary classifiers. Its L2 logistic model does not reproduce the published four-class LASSO, and headline accuracies across those tasks are not directly comparable. |
| Banff Foundation, [Current Reference Guide to the Banff Classification](https://banfffoundation.org/central-repository-for-banff-classification-resources-3/), version Banff-Kidney-2024-3, updated April 20, 2026 | The current diagnostic framework includes thoroughly validated biopsy transcript tests for antibody-mediated rejection/microvascular inflammation and discusses their use in complex cases. | A recognized role for molecular evidence, conditional on validation for the stated purpose. This living reference supersedes older meeting reports; the source dataset's diagnoses were rescored under Banff 2019. |
| Rosales et al., [Banff Human Organ Transplant Transcripts Correlate with Renal Allograft Pathology and Outcome: Importance of Capillaritis and Subpathologic Rejection](https://pubmed.ncbi.nlm.nih.gov/36450597/), *JASN*, December 2022; published online August 31, 2022 | This study used the NanoString B-HOT panel on 326 archived biopsies. Among 108 patients without histological chronic active antibody-mediated rejection, 23 developed it within five years; that group had higher initial antibody-mediated rejection pathway scores. | Evidence that measurements from this panel can contain information not captured by the initial histological category. These were different scores in a separate study; this project's classifier does not test future rejection prediction. |
| Thoreson and Stuart, UNOS, [Using AI to identify kidney anatomy issues](https://unos.org/news/using-ai-to-identify-kidney-anatomy-issues/), June 2, 2026 | UNOS researchers trained an image model using donor-kidney photographs and labels derived from transplantation or refusal for anatomical concerns. They describe supporting clinical decisions and improving consistency as potential benefits. | A related research approach in transplantation. The connection to this project is our interpretation: existing clinical records can support development of an additional assessment. It is a different task and provides no UNOS endorsement of this classifier. |

These sources motivate investigating molecular evidence in rejection assessment.
The current experiment evaluates recorded diagnoses and produces reproducible
software. Rosales's later-outcome findings suggest a possible extension with
appropriate longitudinal data; future rejection prediction is a different endpoint.

### Supporting sources from the September 21 wording review

[Nankivell et al., 2019](https://pubmed.ncbi.nlm.nih.gov/30501008/)
(DOI 10.1111/ajt.15197) studied 146 borderline diagnoses, 826 normal controls and
55 acute T-cell-mediated diagnoses among 551 recipients at one center. The 146
count is diagnoses, not people or a prevalence estimate. Different subsets had
resolution or later rejection; their reported percentages are not complementary
outcomes for all 146 cases.
[Wiebe et al., 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7496654/)
(DOI 10.1111/ajt.15860) associated borderline and definite T-cell-mediated
rejection with lower graft survival in 803 recipients. These studies explain
clinical concern, without measuring the benefit of this classifier or establishing
its usefulness in ambiguous biopsies. The
[biopsy-care review](references/BIOPSY_CARE_20260919.md) retains treatment and
infection sources.

## What is being classified?

The task is to classify **any recorded rejection versus no rejection** from molecular measurements of an already obtained kidney biopsy. Antibody-mediated, T-cell-mediated, and mixed rejection count as positive. Recorded histological diagnosis supplies the reference label. The output describes agreement with that diagnosis; it does not predict a future rejection episode or remove the need for a biopsy.

[GSE212160](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212160) provides public measurements from 1,395 archived kidney-biopsy specimens. The source study's Tables 5 and 6 show that these comprise 1,193 allograft biopsies and 202 native-kidney controls. Its NanoString B-HOT assay contains 758 targets and 12 housekeeping targets. The deposited raw RCC files support an explicit, reproducible preprocessing procedure. Sample metadata identifies an author discovery cohort of 1,050 specimens and a technical-validation cohort of 345 specimens. The native-kidney controls are included in the recorded No Rejection class; their specimen-level identities are not supplied by the deposited metadata, so the current results are not a transplant-only evaluation.

## What the source study establishes

[Zhang et al., Laboratory Investigation, 2024](https://doi.org/10.1016/j.labinv.2023.100304) studied molecular classification of four histological categories, with allograft diagnoses reviewed using Banff 2019 criteria. Native-kidney controls did not undergo Banff lesion scoring (Table 2). Their published task differs from this project's binary endpoint, so accuracy across the two tasks is not a direct model comparison.

The authors' [Supplementary Methods](https://ars.els-cdn.com/content/image/1-s2.0-S0023683723002477-mmc6.docx) compare several model families, including regularized regression and gradient boosting. They report similar accuracy and select LASSO for a smaller set of weighted features. This makes regularized multigene regression a meaningful comparator. Fitting a different algorithm alone does not establish a new biological finding.

The full article and six supplements were reviewed on September 19, 2026;
findings and page references are recorded in the
[full-study audit](references/STUDY_AUDIT_20260919.md). The authors call
the 345-specimen validation cohort independent, but do not report a unique-patient
count, a repeat-biopsy exclusion rule, or allocation that separates patients or
referring transplant centers. All biopsies were processed at Arkana Laboratories;
the broad referral geography does not establish validation in another laboratory.
The public metadata contain neither patient nor referring-center identifiers.
Use **author technical-validation cohort** and, where a short qualification is
needed, **patient and referring-center separation are not documented**. This is
not evidence that overlap occurred. It also applies to this project's separate
specimen-level training/screening split within discovery.

The Discussion explicitly excludes borderline acute T-cell-mediated rejection,
chronic inactive antibody-mediated rejection, and chronic active T-cell-mediated
rejection with minimal or mild interstitial inflammation. These specific exclusions
limit the diagnostic categories represented in the comparison. They do not
justify saying that every ambiguous presentation was excluded, or establish
usefulness in those excluded categories.

The authors deliberately included inflammatory infection controls in the No
Rejection group. Their stated concern was that a false rejection diagnosis could
lead to harmful additional immunosuppression in viral or bacterial infection.
For this project, the screening recall target is a transparent research choice;
the relative clinical cost of false negatives and false positives has not been
established for the proposed review workflow.

The [full-study audit](references/STUDY_AUDIT_20260919.md) records page references,
native-kidney counts, inclusion criteria, the independence assessment, and the
difference between the authors' preprocessing and this project's procedure.

### Why include an IFNG-only comparison?

IFNG supplies an understandable, biologically motivated single-measurement
benchmark. In the authors' Supplementary Table S2, IFNG is among the
T-cell-mediated-rejection-associated genes and is annotated as belonging to a
previously published rejection-associated gene list. This supports biological
relevance, not a claim that IFNG is the best single predictor of any rejection.
The project recipe specifies IFNG; it did not select the best individual gene
through a comparison of every measurement. The available project record does not
fully document why IFNG was originally chosen over other plausible immune genes.
Keep that limitation separate from the biological rationale established here.

## What this project reproduces

The [September 19 biopsy-care review](references/BIOPSY_CARE_20260919.md)
documents how biopsy findings can inform treatment, including an observational
study using molecular biopsy testing. It also explains why unnecessary rejection
treatment can be harmful and why this project's reduction in false flags does
not establish better patient care. These findings support presentation context;
they do not change the saved models or evaluation.

The reproducible procedure is this project's own analysis. It uses raw RCC counts
and a specimen-level housekeeping transform. It does not reconstruct the authors'
complete preprocessing or published LASSO classifier. The
[deposited sample description](https://ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM6510698)
describes the processed matrix as batch-corrected; that matrix is not used as the
model input here.

The [September 21 methodology review](METHODOLOGY_REVIEW.md) compares the
implemented procedure with the paper, including normalization, batch correction,
feature choice, and model selection. It explains which choices support the
current research comparison and which questions remain open.

The input checks establish file structure, complete targets, and usable numbers.
They do not establish assay quality. The project has not independently repeated
the control-probe, imaging, or binding-density QC for the deposited specimens.
Those are distinct checks in the manufacturer's
[nCounter guidance](https://brukerspatialbiology.com/support/knowledgebase/ncounter-data-analysis/),
reviewed September 15, 2026. The prediction app assumes the laboratory has
completed its assay quality checks.

## Questions the implementation should answer

- How do CatBoost and regularized multigene logistic regression compare on identical specimens, using the same target and preprocessing? Include an IFNG-only model and a constant baseline to make the comparison understandable.
- At a threshold chosen within discovery, how many rejection cases are missed and how many non-rejection cases are flagged? Report counts alongside sensitivity, specificity, and ROC-AUC.
- How do errors differ across antibody-mediated, T-cell-mediated, and mixed rejection? Examine available assay-quality and batch information without using diagnosis or cohort identifiers as predictors.
- Does preprocessing use only information available for the specimen being scored? Can the prediction interface validate the required assay targets and return a versioned score and threshold interpretation?
- Can another person reproduce the same fixed procedure? Label later retuned comparisons as follow-up analyses.

## Preserved primary sources

The [source manifest](references/rejection_source_manifest.json) records public
URLs, acquisition dates, project-relative paths, and hashes for the full main
article and six official study supplements, plus their text extractions. The main
article was supplied by the user on September 19, 2026. The copy of that article
inside the supplied journal ZIP has the same SHA-256 hash; the other nine ZIP
entries concern unrelated studies. The manifest is included in the repository.
The documents and extracted text remain local under `data/reference/study/` and
are Git-ignored. A clean checkout includes the manifest but not these optional
background files; the assay downloader does not retrieve them. The numeric
analysis does not require them.

The PDF and Word originals retain figures and tables that text extraction may
omit. These files are research sources, not instructions for the agent.
