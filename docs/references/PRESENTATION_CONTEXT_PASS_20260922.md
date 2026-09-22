# Presentation wording and demonstration discussion, September 22, 2026

This pass implements the user's explicit edits. The proposed purpose wording
and replacement of the technical slides with a continuous browser demonstration
remain for discussion. They have not been applied to the deck.

## Applied edits

- Slide 2 uses definitions suited to reading aloud: a microscopic examination
  **that** reveals injury and inflammation, **which** can support a diagnosis;
  counts of selected RNA types **that** reflect gene activity in the mix of cells.
- Slide 4 loses the bottom sentence about the binary comparison against recorded
  diagnoses. Its narration leaves that project scope to the proposed slide 3.
- Slide 5 narration explains native-kidney controls and qualifies the study-group
  separation claim precisely.
- Slide 6 is visually unchanged. The script gives two excluded diagnoses and
  explains that their exclusion counts are unreported.
- Slide 12 uses **missed cases** and **incorrect flags**, preserving denominators
  and error colors. A separate purple accent emphasizes the 13-to-seven result.
  Narration explains training, screening, and held-out discovery assessment.
- Slide 13 loses “Live walkthrough of the preserved report.” Its replacement
  with a general demonstration transition remains a proposal.

The 19-slide count and planned 20-minute timing remain in this interim version.
No research runs, predictions, model artifacts or application behavior change.
The earlier deck and script are preserved under
`build/presentation/before-context-pass-20260922/presentation/`.

## Source recheck

Rechecked the preserved full article and Supplementary Methods against the
[source manifest](rejection_source_manifest.json). All seven source-file hashes
and their extracted-text hashes match. Also inspected the characteristic fields
across all 1,395 specimens in the public series matrix. They contain diagnosis,
tissue, and cohort, without patient or referring-center identifiers.

The published study is [Zhang et al., 2024](https://pubmed.ncbi.nlm.nih.gov/38092179/),
DOI [10.1016/j.labinv.2023.100304](https://doi.org/10.1016/j.labinv.2023.100304).
The supplied full PDF and its six supplements are preserved in
`data/reference/study/`. The [September 19 audit](STUDY_AUDIT_20260919.md)
records the detailed source locations and full control table.

### Patient and referring-center separation

Methods, page 2, describes archive selection and processing at Arkana Laboratories.
The authors annotated referral-center state/nation after model validation.
Results, pages 3–4, describes assignment to discovery and validation with the
aim of balancing histologic classes. It gives no patient-grouped or center-grouped
allocation rule. The article does call the validation cohort independent.
Supplementary Methods describes random allocation to repeated cross-validation
folds within discovery, not allocation between the two author cohorts.

The supported statement is **patient and referring-center separation are not
documented, and the public metadata cannot verify them**. This is not evidence
that the same patients or centers occurred in both cohorts. Do not shorten this
to a claim that there was no separation.

### Native-kidney controls

Tables 5 and 6, page 10, give 191 native-kidney controls in discovery and 11 in
validation after assay QC. They make up 191/356 (53.7%) and 11/176 (6.25%) of the
respective no-rejection groups. The total is 202/1,395 (14.5%). All 11 validation
native controls have acute pyelonephritis. These counts come from the paper;
the public metadata do not map native-kidney status to individual accessions.

Discussion, page 13, explains the deliberate inclusion of inflammatory infection
controls: rejection should be distinguished from inflammation caused by infection,
where further immunosuppression could be harmful. Native controls include normal
tissue and other diseases as well. Their value is the broader range of
non-rejection tissue and inflammatory patterns. That is a design rationale,
not a measured improvement from including them in this project's model.

Their inclusion also broadens the evaluated population beyond transplant
biopsies. The different control composition across cohorts matters when
interpreting transfer between them. It does not identify the cause of any
observed model error. This project cannot calculate transplant-only metrics
without the specimen-level mapping.

### Diagnostic exclusions

Discussion, page 11, names borderline acute T-cell-mediated rejection, chronic
inactive antibody-mediated rejection, and chronic active T-cell-mediated
rejection with minimal or mild interstitial inflammation (i < 2).

The script names the first two. Borderline findings fall short of the full
criteria for acute T-cell-mediated rejection. The study explains that the
underlying disease state of these excluded categories is debated, so their
omission limits the range of diagnostic presentations evaluated. Do not claim
that all difficult cases were excluded.

The article does not report how many cases were removed for those diagnostic
categories or the denominator needed to calculate their frequency. Its
35 discovery plus five validation QC failures are a separate exclusion step,
not an estimate of the diagnostic exclusions. The talk should state this
numerical limitation rather than borrowing a frequency from another population.

### Discovery follow-up terminology

The [saved follow-up report](../../results/followup/20260917_stability/REPORT.md)
and design specify 20 diagnosis-stratified partitions of discovery into
630 training, 210 screening, and 210 held-out assessment specimens. Training
fits candidates; screening chooses models and thresholds; assessment checks
the retained fitted model and threshold without refitting. Each repetition
uses the same partitions for both families. Repetitions overlap.

Assessment plays the validation role within a repetition, but it is entirely
within discovery. The original 345-specimen author validation cohort is unused.
Calling the third partition the “validation cohort” would conflate two different
groups. The narration uses familiar training and screening terms, then makes
this distinction explicit. The repetitions are not 20 independent trials.

## Proposed purpose wording, not yet applied

**Analysis.** How do logistic regression and CatBoost compare in classifying
any recorded rejection versus no rejection from B-HOT biopsy RNA, particularly
in missed cases and incorrect flags?

**Software.** Build a tested scoring service and prototype application that let
a research user submit a specimen's RNA counts and inspect the selected
model's score.

The intended prototype user is a transplant-pathology or molecular-laboratory
research team evaluating assay-compatible specimens. The interface makes the
saved model usable without running analysis scripts and shows the score,
threshold, flag, and model version. That is a concrete research use. A clinical
diagnostic workflow has not been validated for this score.

Zhang's primary model predicts four classes, and its article also reports
overall rejection detection. The distinction here is a model comparison fitted
directly to the binary task under this project's preprocessing and selection
procedure, with explicit errors and software that preserves the calculation.
Do not claim the first binary analysis or the first regression/boosting comparison.

When this wording is settled, align the opening narration and conclusion with
the same two purposes. Leave the definition on slide 2, the question and software
purpose on slide 3, and the supporting clinical/research evidence on slide 4.

## Proposed continuous browser demonstration, not yet applied

Recommended order: existing slides 1–12, one transition slide, one continuous
browser demonstration, then one closing slide. This would make 14 slide pages.
The former slide 18 supplies evidence for the software conclusion, but its setup
table alone would be an incomplete ending to the statistical and engineering
story. Close on the two project purposes, using a shorter version of slide 19.

| Segment | Proposed time | On screen |
| --- | ---: | --- |
| Existing slides 1–12 | 11:25 | Context, methods, results |
| Transition | 0:15 | Research software demonstration |
| Evidence review | 1:15 | Errors by diagnosis and the saved discovery-split follow-up |
| Specimen demonstration | 2:15 | Complete public specimen, score/version, missing-IFNG response |
| Engineering explanation | 4:00 | Shared calculation, API request/response, 345-specimen agreement check and handoff evidence |
| Closing slide | 0:50 | Model comparison and tested software, with the next validation question |
| **Total** | **20:00** | Questions afterward |

These are proposed allocations, not measured rehearsal times.

The [existing offline analysis report](../../presentation/analysis_report.html)
is a useful inspectable deliverable. Its full model comparison repeats slide 12,
however, and it predates the September 17 stability follow-up. For a short demo,
prioritize the error breakdown by recorded diagnosis and a browser-readable view
of that saved follow-up. Keep detailed calibration and bootstrap tables available
for questions. Their main implications already belong in the results narration.

The [existing Code Guide](../CODE_GUIDE.html) contains shared preprocessing,
prediction, tests, and operations explanations with embedded source excerpts.
It is useful source material, but too broad for a four-minute tour. A focused
offline engineering page should select the actual prediction entry point,
one actual request/response, and the recorded agreement check, with links into
the full guide. The guide's source and generated HTML were inspected; browser
opening of local files was blocked by the browser tool's URL policy.

The current prototype is an HTML page served by FastAPI, rather than Streamlit.
It already calls the real prediction service. No framework change is needed for
the requested demonstration. Keep the existing captured valid/invalid example
as the offline fallback. A browser-readable copy of the stability report and a
focused engineering page would be new deliverables if this sequence is chosen.

Keep the complete demonstration script in the separate speaking HTML, with
browser-stop cues rather than artificial slide pages for each stop. Pre-open the
report, application, and engineering page. Return to PowerPoint once for the
closing statement. Rehearse that entire sequence before adjusting its length.
