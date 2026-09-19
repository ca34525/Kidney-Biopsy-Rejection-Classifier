# Research context

Public-source context first captured on 2026-09-15; clinical rationale updated
2026-09-18; full source study reviewed on 2026-09-19. This document defines the research question and its motivation. Model
findings must come from runs performed in this project.

## Why a molecular second opinion could be useful

The intended application is to support the review of kidney transplant biopsies
whose conventional interpretation is uncertain. Histology examines tissue
appearance; RNA measurements describe gene activity within that tissue. A molecular
assessment could supply additional evidence when microscopic findings are
borderline, incomplete, or inconsistent with other clinical information. The
practical aim is to get more useful information from tissue already collected.

This project develops an early research prototype for that application. It tests
whether molecular measurements identify recorded rejection diagnoses, compares
models, and provides tested software for reproducible scoring. Agreement with
established diagnoses is a useful development step before studying difficult
cases. Showing that the score improves interpretation in those cases requires a
separate evaluation: compare the standard assessment with and without molecular
information, using independent case review or outcomes to judge added value.

The sources below support this motivation. They do not validate this project's
classifier for clinical use.

### Evidence supporting the application

All three sources were checked on **2026-09-18**.

| Source and date | What it supports | Scope of the evidence |
| --- | --- | --- |
| Banff Foundation, [Current Reference Guide to the Banff Classification](https://banfffoundation.org/central-repository-for-banff-classification-resources-3/), version Banff-Kidney-2024-3, updated April 20, 2026 | The current diagnostic framework includes thoroughly validated biopsy transcript tests for antibody-mediated rejection/microvascular inflammation and discusses their use in complex cases. | A recognized role for molecular evidence, conditional on validation for the stated purpose. This living reference supersedes older meeting reports; the source dataset's diagnoses were rescored under Banff 2019. |
| Rosales et al., [Banff Human Organ Transplant Transcripts Correlate with Renal Allograft Pathology and Outcome: Importance of Capillaritis and Subpathologic Rejection](https://pubmed.ncbi.nlm.nih.gov/36450597/), *JASN*, December 2022; published online August 31, 2022 | This study used the NanoString B-HOT panel on 326 archived biopsies. Among 108 patients without histological chronic active antibody-mediated rejection, 23 developed it within five years; that group had higher initial antibody-mediated rejection pathway scores. | Evidence that measurements from this panel can contain information not captured by the initial histological category. These were different scores in a separate study; this project's classifier does not test future rejection prediction. |
| Thoreson and Stuart, UNOS, [Using AI to identify kidney anatomy issues](https://unos.org/news/using-ai-to-identify-kidney-anatomy-issues/), June 2, 2026 | UNOS researchers trained an image model using donor-kidney photographs and labels derived from transplantation or refusal for anatomical concerns. They describe supporting clinical decisions and improving consistency as potential benefits. | A related research approach in transplantation. The connection to this project is our interpretation: existing clinical records can support development of an additional assessment. It is a different task and provides no UNOS endorsement of this classifier. |

The strongest supported project claim is therefore: **a reproducible molecular
classifier is an early step toward a molecular second opinion for uncertain
transplant biopsies**. The present evaluation establishes classification performance
against recorded diagnoses; the proposed benefit in difficult cases remains the
next research question.

## What is being classified?

The task is to classify **any histologically defined rejection versus no rejection** from molecular measurements of an already obtained kidney transplant biopsy. Antibody-mediated, T-cell-mediated, and mixed rejection count as positive. Histological diagnosis supplies the reference label. The output describes agreement with that diagnosis; it does not predict a future rejection episode or remove the need for a biopsy.

[GSE212160](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212160) provides public measurements from 1,395 archived kidney-biopsy specimens. The source study's Tables 5 and 6 show that these comprise 1,193 allograft biopsies and 202 native-kidney controls. Its NanoString B-HOT assay contains 758 targets and 12 housekeeping targets. The deposited raw RCC files support an explicit, reproducible preprocessing procedure. Sample metadata identifies an author discovery cohort of 1,050 specimens and a technical-validation cohort of 345 specimens. The native-kidney controls are included in the recorded No Rejection class; their specimen-level identities are not supplied by the deposited metadata, so the current results are not a transplant-only evaluation.

## What the source study establishes

[Zhang et al., Laboratory Investigation, 2024](https://doi.org/10.1016/j.labinv.2023.100304) studied molecular classification of four histological categories, with allograft diagnoses reviewed using Banff 2019 criteria. Native-kidney controls did not undergo Banff lesion scoring (Table 2). Their published task differs from this project's binary endpoint, so accuracy across the two tasks is not a direct model comparison.

The authors' [Supplementary Methods](https://ars.els-cdn.com/content/image/1-s2.0-S0023683723002477-mmc6.docx) compare several model families and select LASSO for a smaller set of weighted features. This makes regularized multigene regression a meaningful comparator. Fitting a different algorithm alone does not establish a new biological finding.

The full article and all six supplements have now been reviewed. The authors call
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
strengthen the need for a direct study of the proposed uncertain-biopsy use. They
do not justify saying that every ambiguous presentation was excluded.

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

The input checks establish file structure, complete targets, and usable numbers.
They do not establish assay quality. The project has not independently repeated
the control-probe, imaging, or binding-density QC for the deposited specimens.
Those are distinct checks in the manufacturer's
[nCounter guidance](https://brukerspatialbiology.com/support/knowledgebase/ncounter-data-analysis/),
reviewed September 15, 2026. The prediction app assumes the laboratory has
completed its assay quality checks.

## Questions the implementation should answer

- Does CatBoost improve on regularized multigene logistic regression on identical specimens, using the same target and preprocessing? Include an IFNG-only model and a constant baseline to make the comparison understandable.
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
