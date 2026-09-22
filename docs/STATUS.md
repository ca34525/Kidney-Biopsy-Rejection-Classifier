# Current project status

Updated September 22, 2026. Start here for the current reading order; dated run
reports and verification records remain evidence of what was checked at the time.

## Read the project in this order

1. **Purpose and question:** Whether rejection is present can affect decisions
   about further treatment to suppress the immune system. A molecular score could
   supply additional evidence during that assessment. Compare logistic regression
   and CatBoost against recorded diagnoses, emphasizing missed cases and incorrect
   flags. Give equal prominence to reproducible analysis software, the tested
   scoring service and prototype application. The [research context](RESEARCH_CONTEXT.md)
   explains the potential use and what this project evaluates. The
   [README](../README.md) states the input and results.
2. **Primary result:** The [frozen analysis](../results/analysis/20260915_baseline/REPORT.md)
   compares the same 345 specimens. CatBoost missed 25 of 169 rejection cases and
   falsely flagged 8 of 176 no-rejection cases. Logistic regression missed 33 with
   8 false flags; its practical difference from CatBoost remains uncertain.
   These 345 specimens include 334 transplant biopsies and 11 native-kidney
   controls, as established by the [full-study source review](references/STUDY_AUDIT_20260919.md).
   [Presentation figures](../results/presentation/20260917_evidence/README.md) show
   these preserved results with larger labels and editable SVG text.
   The [discovery-only follow-up](../results/followup/20260917_stability/REPORT.md)
   then tests how model choice varies with the development split: CatBoost was
   selected in 13 of 20 repetitions and logistic regression in 7. The overlapping
   repetitions support treating logistic as a credible simpler alternative; they
   are not independent validation trials.
3. **Frozen service:** Run the [local demonstration](API.md). CLI and API default
   to `results/reproduction/20260915_shared`, which reproduces the primary scores.
   Its model and threshold remain fixed. Follow one request through the
   [code guide](CODE_GUIDE.md): read counts, validate, normalize, score, apply threshold.
   The [public-specimen walkthrough](API.md#follow-the-specimen) makes this path
   visible with actual counts and the recorded label kept separate from predictors.
4. **Checks:** The [verification guide](VERIFICATION.md) separates local tests,
   agreement across interfaces, container checks, and hosted CI. See the dated
   evidence below; a previous passing revision is not a test of later edits.
5. **Presentation draft:** The [presentation package](../presentation/README.md)
   contains the editable deck, matching PDF, separate HTML speaking script, and
   continuous engineering HTML demonstration and saved responses for offline use.
   The revised talk has 14 main slides and no backup slides, with a full script
   planned for 20 minutes including 7:30 in the browser. The September 21
   revision restores Banff and preserves the screening counts, validation
   advantage and split-stability evidence. The September 22 purpose revision
   gives the treatment-related motivation and equal model-comparison and
   software-engineering aims on slide 3. Cross-validation remains
   a proposed follow-up. After transition slide 13, the
   [engineering demonstration](../presentation/engineering_demo.html) covers
   saved evidence, a public specimen in the application, shared preparation,
   the API, verification and handoff. Return to closing slide 14 afterward.
   Full reports, the Code Guide and saved check records are included in the HTML
   reference library. Slide 4 includes the KDIGO treatment connection, and slide
   12 uses teal emphasis consistent with the rest of the deck.
   PowerPoint notes are not used. Two full timed rehearsals and one
   interruption/fallback rehearsal remain pending.
   The [AWS guide](AWS_DEPLOYMENT.md) is a procedure; a cloud deployment has not
   been performed. [Next steps](NEXT_STEPS.md) records deferred research questions
   and product ideas without adding them to the current implementation.

## Evidence available

| Evidence | What it establishes | Revision or limitation |
| --- | --- | --- |
| [Primary analysis](../results/analysis/20260915_baseline/REPORT.md) | Same-row comparison, error review, uncertainty, score reliability | Includes native-kidney controls; patient and referring-center separation between cohorts is not documented |
| [September 19 source review](references/STUDY_AUDIT_20260919.md) | Full article and supplements establish transplant/native-kidney counts and clarify cohort limits | Public metadata do not identify native-kidney specimens individually; all biopsies were processed at Arkana Laboratories |
| [September 21 methodology review](METHODOLOGY_REVIEW.md) | Compares the implemented methods with the paper and records the remaining weaknesses | Assessment of the existing procedure; no new model fitting or clinical evaluation |
| [Discovery-only stability](../results/followup/20260917_stability/REPORT.md) | Model choice changes across 20 development splits; 100 fits completed in 639.3 seconds | Each split uses 630 fit / 210 screen / 210 assessment specimens; no author-validation scoring or service change |
| [Fixed-procedure reproduction](../results/checks/20260915_readability/reproduction.json) | All nine prediction tables, model choices, and thresholds reproduced exactly | A repeat of the fixed procedure, not a new validation cohort |
| [HTTP comparison](../results/checks/20260915_readability/http/http.json) | CLI, API, and saved scores agree on all 345 validation specimens | Software consistency, not new classifier evaluation |
| [Current application checks](../results/checks/20260917_coherence/README.md) | 94 installed-package tests; Ruff on 35 Python files; all 345 HTTP/CLI scores agree; rebuilt research container verifies four public walkthroughs | Local checks on the current walkthrough and consistency changes; no cloud deployment |
| [Local CI/container checks](../results/checks/20260917_ci_docker/README.md) | 78 tests passed; research and synthetic images served verified predictions | Completed before the current walkthrough and stability additions |
| [Hosted Software checks #8](https://github.com/ca34525/Kidney-Biopsy-Rejection-Classifier/actions/runs/35270209322) | Installed package, lint, tests, and synthetic-container checks succeeded | PR #2 head `ce34d4c79442098308c89ca4ccb34542c4010216`; previous revision |
| [Subtype follow-up](../results/followup/20260915_subtypes/REPORT.md) | Four-class comparisons did not justify replacing the binary service | Follow-up on an already examined validation cohort |
| [Viral-target review](../results/analysis/20260915_viral/REPORT.md) | Describes BK signals and study composition | No viral-feature removal or independent assay-QC experiment |
| [Presentation draft](../presentation/README.md) | 19 editable slides, matching PDF, separate HTML script, offline report, and static demo fallback | Comparative question and model-selection explanation revised; no backup slides; 20-minute timing is planned and rehearsals remain pending |

The September 17 application work added a walkthrough
of a prepared public specimen, a bounded discovery-only stability comparison,
larger evidence figures, and consistency fixes. The
[current local check record](../results/checks/20260917_coherence/README.md) is
separate from the previous hosted pass. Rechecking nine preserved prediction
tables found zero differences; all 167 preserved run artifacts match their
original manifests. The frozen service model and threshold are unchanged.

The September 19 presentation and source pass revised the slide sequence and
checked the full study and supplements. The 1,395 specimens include 1,193
transplant biopsies and 202 native-kidney controls, some with native-kidney disease.
The updated population description qualifies the existing results; it does not
change saved runs. Timed rehearsals remain pending.

The September 21 review reconciles the dated source-review statement, adds the
native-control qualification to the demo and future generated reports, and
corrects the presentation's constant-threshold and logistic-setting descriptions.
The [methodology comparison](METHODOLOGY_REVIEW.md) explains the defensible choices
and the remaining weaknesses. The [correction checks](../results/checks/20260921_source_review/README.md)
record software and presentation checks and confirm that the preserved baseline
and service run artifacts are intact.

## Keep the main story short

The intended use, data question, fair comparison, observed errors, and working
prediction path form the main talk. Keep the subtype follow-up, detailed
reliability tables, assay-group tables, and implementation history available for
questions. The completed work supplies a reproducible prototype for further
evaluation. A direct comparison of usual assessment with and without molecular
scores during rejection assessment would test its added benefit. Independent-cohort
evaluation and laboratory quality checks would strengthen that study.

Background: [project specification](PROJECT_SPEC.md), [research context](RESEARCH_CONTEXT.md),
[job requirements](JOB_REQUIREMENTS.md), [plan](PLAN.md), [presentation guide](PRESENTATION_GUIDE.md),
and [public-source manifest](../data/manifest.json).
