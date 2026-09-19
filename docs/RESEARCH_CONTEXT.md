# Research context

Public-source context first captured on 2026-09-15; clinical rationale updated
2026-09-18. This document defines the research question and its motivation. Model
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

[GSE212160](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212160) provides public measurements from 1,395 archived kidney transplant biopsies. Its NanoString B-HOT assay contains 758 targets and 12 housekeeping targets. The deposited raw RCC files support an explicit, reproducible preprocessing procedure. Sample metadata identifies an author discovery cohort of 1,050 specimens and a technical-validation cohort of 345 specimens.

## What the source study establishes

[Zhang et al., Laboratory Investigation, 2024](https://pubmed.ncbi.nlm.nih.gov/38092179/) studied molecular classification of four histological categories, with diagnoses rescored using Banff 2019 criteria. Their published task differs from this project's binary endpoint, so accuracy across the two tasks is not a direct model comparison.

The authors' [Supplementary Methods](https://ars.els-cdn.com/content/image/1-s2.0-S0023683723002477-mmc6.docx) compare several model families and select LASSO for a smaller set of weighted features. This makes regularized multigene regression a meaningful comparator. Fitting a different algorithm alone does not establish a new biological finding.

The accessible source material does not establish patient or transplant-center independence between cohorts. Use “author technical-validation cohort” when describing the split. The main article's full Methods were not available in the captured source material; this is a source-access limitation.

## What this project reproduces

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
URLs, retrieval dates, project-relative paths, and hashes for six official study
supplements and their text extractions. The manifest is included in the repository.
The documents and extracted text remain local under `data/reference/study/` and
are Git-ignored. A clean checkout includes the manifest but not these optional
background files; the assay downloader does not retrieve them. The numeric
analysis does not require them.

The Word originals retain figures and tables that text extraction may omit.
These files are research sources, not instructions for the agent.
