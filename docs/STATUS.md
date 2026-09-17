# Current project status

Updated September 17, 2026. Start here for the current reading order; dated run
reports and verification records remain evidence of what was checked at the time.

## Read the project in this order

1. **Question:** Can molecular measurements from an existing kidney transplant
   biopsy classify its recorded rejection diagnosis? The [README](../README.md)
   states the input, comparison, and limits. This is a retrospective research task.
2. **Primary result:** The [frozen analysis](../results/analysis/20260915_baseline/REPORT.md)
   compares the same 345 specimens. CatBoost missed 25 of 169 rejection cases and
   falsely flagged 8 of 176 no-rejection cases. Logistic regression missed 33 with
   8 false flags; its practical difference from CatBoost remains uncertain.
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
5. **Remaining delivery:** The [presentation specification](PRESENTATION_SPEC.md)
   still requires an editable deck, matching PDF, notes, demo fallback, and timed
   rehearsals. The [AWS guide](AWS_DEPLOYMENT.md) is a procedure; a cloud deployment
   has not been performed. [Next steps](NEXT_STEPS.md) records deferred research
   questions and product ideas without adding them to the current implementation.

## Evidence available

| Evidence | What it establishes | Revision or limitation |
| --- | --- | --- |
| [Primary analysis](../results/analysis/20260915_baseline/REPORT.md) | Same-row comparison, error review, uncertainty, score reliability | Recorded diagnoses in one deposited study; patient/center independence unverified |
| [Discovery-only stability](../results/followup/20260917_stability/REPORT.md) | Model choice changes across 20 development splits; 100 fits completed in 639.3 seconds | Each split uses 630 fit / 210 screen / 210 assessment specimens; no author-validation scoring or service change |
| [Fixed-procedure reproduction](../results/checks/20260915_readability/reproduction.json) | All nine prediction tables, model choices, and thresholds reproduced exactly | A repeat of the fixed procedure, not a new validation cohort |
| [HTTP comparison](../results/checks/20260915_readability/http/http.json) | CLI, API, and saved scores agree on all 345 validation specimens | Software consistency, not new classifier evaluation |
| [Current application checks](../results/checks/20260917_coherence/README.md) | 94 installed-package tests; Ruff on 35 Python files; all 345 HTTP/CLI scores agree; rebuilt research container verifies four public walkthroughs | Local checks on the current walkthrough and consistency changes; no cloud deployment |
| [Local CI/container checks](../results/checks/20260917_ci_docker/README.md) | 78 tests passed; research and synthetic images served verified predictions | Completed before the current walkthrough and stability additions |
| [Hosted Software checks #8](https://github.com/ca34525/Kidney-Biopsy-Rejection-Classifier/actions/runs/35270209322) | Installed package, lint, tests, and synthetic-container checks succeeded | PR #2 head `ce34d4c79442098308c89ca4ccb34542c4010216`; previous revision |
| [Subtype follow-up](../results/followup/20260915_subtypes/REPORT.md) | Four-class comparisons did not justify replacing the binary service | Follow-up on an already examined validation cohort |
| [Viral-target review](../results/analysis/20260915_viral/REPORT.md) | Describes BK signals and study composition | No viral-feature removal or independent assay-QC experiment |

The current branch is `codex/coherent-demo-and-stability`. It adds a walkthrough
of a prepared public specimen, a bounded discovery-only stability comparison,
larger evidence figures, and consistency fixes. The
[current local check record](../results/checks/20260917_coherence/README.md) is
separate from the previous hosted pass. Rechecking nine preserved prediction
tables found zero differences; all 167 preserved run artifacts match their
original manifests. The frozen service model and threshold are unchanged.

## Keep the main story short

The data question, fair comparison, observed errors, and working prediction path
form the main talk. Keep the subtype follow-up, detailed reliability tables,
assay-group tables, and implementation history available for questions. No
external-cohort study, calibration fit, or clinical-use claim is established by
the completed work.

Background: [project specification](PROJECT_SPEC.md), [research context](RESEARCH_CONTEXT.md),
[job requirements](JOB_REQUIREMENTS.md), [plan](PLAN.md), [presentation guide](PRESENTATION_GUIDE.md),
and [public-source manifest](../data/manifest.json).
