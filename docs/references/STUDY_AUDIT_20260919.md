# Full source-study review, September 19, 2026

The full article supports retaining a narrow independence qualification and
requires a correction to the dataset description: the 1,395 specimens include
202 native-kidney controls. It also explicitly identifies several excluded
diagnostic categories relevant to the proposed uncertain-biopsy application.
No model, split, threshold, prediction, or analysis result was changed for this
source review.

## Sources and review scope

Zhang et al., *Development and Validation of a Multiclass Model Defining Molecular
Archetypes of Kidney Transplant Rejection: A Large Cohort Study of the Banff Human
Organ Transplant Gene Expression Panel*, *Laboratory Investigation* 104 (2024),
100304, [DOI: 10.1016/j.labinv.2023.100304](https://doi.org/10.1016/j.labinv.2023.100304).
The article was available online December 12, 2023. Page numbers below refer to
the PDF's printed pages, which match the PDF page order.

Reviewed the complete 16-page article, the six preserved official supplements,
and the deposited GEO series-matrix sample metadata. The relevant Methods,
cohort diagram, Tables 5 and 6, exclusions, and infection-control discussion were
also checked against rendered PDF pages, not only extracted text.

The user supplied `PIIS0023683723002477.pdf` and
`Laboratory Investigation_20260919.zip`. The ZIP manifest contains ten journal
articles. Its `Development-and-Validation-of-a-Multiclass-Model-D.pdf` entry is
byte-for-byte identical to the separately supplied PDF. The nine other articles
are unrelated studies and were not needed for this review. No archive contents
were executed. All attached material was treated as source evidence, not as
instructions.

The preserved article is `data/reference/study/rejection_main_article.pdf`
(2,641,311 bytes; SHA-256
`e8a500c496834e3fc0af9a0baf5d694fa9be31ba06b03f7edd441202c78218a8`).
Its text extraction is `data/reference/study/rejection_main_article.txt`.
The [source manifest](rejection_source_manifest.json) preserves provenance for
the article and supplements. Source copies are Git-ignored optional background
files; the numeric workflow does not depend on them.

## Patient, center, and laboratory separation

| Question | What the study reports | Supported interpretation |
| --- | --- | --- |
| How were cases selected? | Methods, Cohort Selection, p. 2: archive screening primarily from January 2012 through November 2021, plus rare diagnoses from 2008-2011. Discussion, p. 9: search of consecutive cases, followed by histology-based selection. | A selected retrospective archive sample, not a prospectively enrolled series of all patients seen. |
| Was each patient represented once? | The full article and supplements do not give a unique-patient count, a one-biopsy-per-patient rule, or a repeat-biopsy exclusion rule. | The 1,395 count is specimens. Repeated patients are neither demonstrated nor ruled out. |
| How were author cohorts allocated? | Results, pp. 3-4: 1,085 discovery and 350 validation specimens before QC, aiming to balance histologic class proportions; 1,050 and 345 after QC. The introduction, p. 2, and results, p. 6, call validation independent. Random or chronological cohort allocation is not reported. Supplementary Methods' random allocation refers to cross-validation folds within discovery. | Separate biopsy sets are reported. The allocation description does not establish separation by patient or referring center. |
| Were referring centers held out? | Methods, p. 2: referral-center state/nation was annotated after model validation. Figure 3, p. 5: the combined sample came from 10 of 11 UNOS regions and included seven international specimens. | Geographic coverage is documented; center-held-out evaluation is not. The paper gives no center-allocation rule. |
| Were different laboratories evaluated? | Methods, p. 2: all biopsies were processed at Arkana Laboratories, a national referral pathology practice. | Multiple referral locations do not imply independent assay laboratories. |
| Can the deposited rows verify separation? | GEO metadata provide a specimen title/accession, the four-class diagnosis, generic renal-biopsy tissue, and discovery/validation membership. They do not provide patient or referring-center identifiers. | This project cannot verify patient or referring-center separation from the supplied metadata. Source-contact details are submitter information, not specimen recruitment centers. |

Recommended short slide footnote:

> \*Patient and referring-center separation are not documented; all specimens
> were processed at one laboratory.

The script should distinguish the authors' discovery/technical-validation
division from this project's 787/263 training/screening split within discovery.
The latter is explicitly a specimen-level stratified split, not a patient- or
center-grouped split. Neither a unique specimen ID nor absence of duplicate
expression profiles establishes patient independence. The full article resolves
the previous source-access limitation; uncertainty about these allocation details
remains because they are not reported.

## Native-kidney controls change the population description

Results, p. 3, states that the No Rejection group includes both allograft and
native-kidney biopsies. Tables 5 and 6, p. 10, provide the relevant counts. Use
their **QC pass** column to match the 1,395 deposited specimens.

| Native-kidney subgroup | Discovery, QC pass | Validation, QC pass |
| --- | ---: | ---: |
| Normal | 32 | 0 |
| Thrombotic microangiopathy | 14 | 0 |
| Acute pyelonephritis | 50 | 11 |
| CMV nephritis | 3 | 0 |
| Reactive inflammation in areas of fibrosis | 42 | 0 |
| Diabetic nephropathy | 28 | 0 |
| Smoking-related nodular glomerulosclerosis | 16 | 0 |
| Polyomavirus nephritis | 6 | 0 |
| **Native-kidney total** | **191** | **11** |
| **Allograft total, derived by subtraction** | **859** | **334** |
| **All specimens** | **1,050** | **345** |

There are therefore **202 native-kidney controls and 1,193 allograft specimens**.
Within No Rejection, the counts are 191 native/165 allograft in discovery and
11 native/165 allograft in validation. This difference in control composition is
relevant when interpreting transfer from discovery to validation. It does not
show that native controls caused a particular model error or performance change.

The GEO metadata do not map the native/allograft or detailed histology subgroups
to specimen IDs. The paper supplies group totals, not a row-level mapping. This
review therefore does not remove native controls or produce transplant-only
metrics. Present the existing results as evaluation on the author's full biopsy
cohort, with the composition stated, while retaining transplant assessment as
the intended application.

Recommended dataset description:

> 1,395 kidney-biopsy specimens, including 202 native-kidney controls.

## Label review and exclusions

Methods, p. 2, describes review by expert renal pathologists, Banff 2019 scoring
including rereview of earlier cases, and consensus on disagreements. Table 2,
p. 5, explicitly excludes native-kidney biopsies from Banff lesion scoring.
Describe the **allograft diagnoses** as reviewed under Banff 2019; do not imply
native controls received transplant rejection lesion scores.

The Discussion, p. 11, explicitly excludes:

- Borderline (Suspicious) for Acute TCMR.
- Chronic (Inactive) ABMR.
- Chronic Active TCMR with minimal or mild interstitial inflammation (i < 2).

Methods, p. 2, additionally lists inadequate tissue, more than one histologic
class (for example, polyomavirus nephritis with TCMR grade 2A), concomitant
immune-complex disease except mild IgA deposition, unavailable DSA status in
histologic ABMR despite follow-up, and insufficient residual tissue among the
exclusion criteria. The study nevertheless has a deliberately defined mixed
ABMR/TCMR category. Do not paraphrase its exclusion as excluding all mixed
rejection.

The specific diagnostic exclusions support saying that important uncertain
categories need separate evaluation. They do not establish that every difficult
case was absent. The authors themselves distinguish technical validation from
clinical validity and clinical utility (Discussion, p. 14).

## IFNG and model comparisons

Supplementary Table S2 lists IFNG among TCMR-associated genes: rank 23 by adjusted
p-value, fold change 2.43, FDR-adjusted p-value 7.22e-62, comparing TCMR with the
combined No Rejection and ABMR classes in discovery. Its TCMR-RAT annotation
links it to the authors' previously published rejection-associated transcript
list. This is a biological rationale for an interpretable single-measurement
benchmark, not proof that IFNG is the best individual predictor of the binary
endpoint. The table is an association analysis, not a single-gene classifier
comparison.

Supplementary Table S3 also compares IFNG in TCMR versus allograft polyomavirus
nephritis: fold change 1.40, adjusted p-value .018, rank 61 of 66 genes. Do not
describe IFNG as specific to rejection. It is not among the weighted genes shown
in the authors' final multiclass model, Table 3, pp. 7-9.

The project specification and fixed recipe include IFNG as a separate benchmark.
The available record does not establish a complete original rationale for
choosing it over every other plausible marker. The presentation should state
its role and biological relevance without inventing a historical selection
process or claiming that the study selected IFNG for this project.

Supplementary Methods, Diagnostic Model Fitting, reports comparison of elastic
net/LASSO, random forests, gradient boosting, nearest neighbors, and support
vector machines using the same repeated folds. Comparable accuracy and fewer
weighted genes motivated LASSO. This supports retaining regularized multigene
logistic regression as a meaningful comparator in our different binary task.

## Preprocessing and what is reproduced here

Methods, p. 3, reports normalization to the pooled 1,050-specimen discovery
reference, correction for two assay lots using ComBat-seq, and assay QC criteria
of housekeeping scaling factor below 10 and more than 62% of probes above
detection. The study excluded 35 discovery and five validation specimens that
failed QC. Its model considered 745 features after removing 13 targets annotated
as specific to other organs from the 758 non-housekeeping targets; 143 genes
received nonzero weights in the multiclass model.

Our recipe uses raw counts, a within-specimen housekeeping transform, all 758
non-housekeeping assay targets, and a binary target. It does not reconstruct the
authors' published preprocessing or fitted model. Reproducing our fixed analysis
is separate from reproducing the original publication. The project's numeric
input checks do not repeat the authors' laboratory QC.

## False positives and false negatives

Discussion, p. 13, gives a concrete reason to care about false positives: the
authors included polyomavirus and bacterial infection controls to avoid a
rejection call that could prompt detrimental additional immunosuppression.
False negatives can also matter, but this paper does not supply cost weights
for the proposed review-support workflow.

The project rule of at least 90% screening recall followed by minimizing false
positives is a defensible, explicit research preference. It is neither an
established clinical requirement nor proof of a clinically optimal tradeoff.
The presentation should not claim false negatives are always more costly, and
should make clear that the 90% screening target was not achieved in validation.

## September 22 source recheck

The later review rechecked the preserved article, six supplements and extracted
texts against the source manifest; all seven file and text hashes matched. It
also inspected all 1,395 public metadata records and confirmed the absence of
patient and referring-center identifiers. This records that dated review, not a
new source check during documentation cleanup.

The diagnostic exclusion counts and their denominator are not reported. The
35 discovery and five validation assay-QC failures are a separate exclusion
step and cannot be used to estimate diagnostic exclusions. Tables 5–6 identify
all 11 native-kidney validation controls as acute pyelonephritis. Patient and
referring-center separation are undocumented; that does not prove overlap.
