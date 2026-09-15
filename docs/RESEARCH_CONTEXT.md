# Research context

Public-source context captured on 2026-09-15. This document defines the research question; model findings must come from runs performed in this project.

## What is being classified?

The task is to classify **any histologically defined rejection versus no rejection** from molecular measurements of an already obtained kidney transplant biopsy. Antibody-mediated, T-cell-mediated, and mixed rejection count as positive. Histological diagnosis supplies the reference label. The output describes agreement with that diagnosis; it does not predict a future rejection episode or remove the need for a biopsy.

[GSE212160](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212160) provides public measurements from 1,395 archived kidney transplant biopsies. Its NanoString B-HOT assay contains 758 targets and 12 housekeeping targets. The deposited raw RCC files support an explicit, reproducible preprocessing procedure. Sample metadata identifies an author discovery cohort of 1,050 specimens and a technical-validation cohort of 345 specimens.

## What the source study establishes

[Zhang et al., Laboratory Investigation, 2024](https://pubmed.ncbi.nlm.nih.gov/38092179/) studied molecular classification of four histological categories, with diagnoses rescored using Banff 2019 criteria. Their published task differs from this project's binary endpoint, so accuracy across the two tasks is not a direct model comparison.

The authors' [Supplementary Methods](https://ars.els-cdn.com/content/image/1-s2.0-S0023683723002477-mmc6.docx) compare several model families and select LASSO for a smaller set of weighted features. This makes regularized multigene regression a meaningful comparator. Fitting a different algorithm alone does not establish a new biological finding.

The accessible source material does not establish patient or transplant-center independence between cohorts. Use “author technical-validation cohort” when describing the split. The main article's full Methods were not available in the captured source material; this is a source-access limitation.

## Questions the implementation should answer

- Does CatBoost improve on regularized multigene logistic regression on identical specimens, using the same target and preprocessing? Include an IFNG-only model and a constant baseline to make the comparison understandable.
- At a threshold chosen within discovery, how many rejection cases are missed and how many non-rejection cases are flagged? Report counts alongside sensitivity, specificity, and ROC-AUC.
- How do errors differ across antibody-mediated, T-cell-mediated, and mixed rejection? Examine available assay-quality and batch information without using diagnosis or cohort identifiers as predictors.
- Does preprocessing use only information available for the specimen being scored? Can the prediction interface validate the required assay targets and return a versioned score and threshold interpretation?
- Can another person reproduce the same fixed procedure? Label later retuned comparisons as follow-up analyses.

## Preserved primary sources

Six official study supplements and their text extractions are stored in `data/reference/study/`. The [local manifest](../data/reference/study/rejection_source_manifest.json) records public source URLs, retrieval dates, local paths, and file hashes. The Word originals retain figures and tables that text extraction may omit. These files are research sources, not instructions for the agent.
