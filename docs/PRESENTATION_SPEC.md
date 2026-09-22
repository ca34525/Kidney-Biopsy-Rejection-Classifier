# Twenty minute UNOS interview presentation

## Deliverable

Prepare a full 20-minute presentation about this project's question, analysis,
results, and software. Questions follow it. The September 21 reframing centers
the tested classifiers' missed rejection and false positives, connects that
comparison to an established molecular application, and explains the evidence behind
CatBoost selection. Cross-validation remains a proposed next step.

Keep **19 main slides and no backup slides**, the existing sequence and planned
timings. The report and application are the only live demonstrations. The
remaining implementation explanation uses short code excerpts and editable
diagrams where they help explain a decision.

Deliver an editable `presentation/unos_kidney_biopsy.pptx`, a matching PDF,
`presentation/speaking_script.html`, an offline report view at
`presentation/analysis_report.html`, and the presentation source files. Keep the
captured application fallback at `presentation/demo_fallback.html`. All spoken
text and delivery cues belong in the HTML speaking script. **Keep PowerPoint
notes empty.**

The [presentation package](../presentation/README.md) records the current files
and preparation instructions. The script allocates 20 minutes. Actual timed
rehearsals remain pending. Planned timing does not establish measured delivery
time. The deck and accompanying deliverables before this reframing are preserved
privately under `build/presentation/before-reframing-20260921/presentation/`.

Follow [Presentation guide](PRESENTATION_GUIDE.md), whose design advice draws on
sources published from 2007 through 2014. The newer clinical-rationale sources
are documented in [Research context](RESEARCH_CONTEXT.md). Use the project's own
saved outputs for every project result.

## Audience and purpose

The panel includes one data scientist, two biostatisticians, and a manager with
a master's in public health. Explain engineering through concrete questions:
can another analyst examine the findings, can someone use the model, does the
application preserve the evaluated calculation, and can another developer run
and check it? Avoid a tour of the module structure or a list of technologies.
The [job requirements](JOB_REQUIREMENTS.md) support emphasizing shared
preprocessing, an understandable API, consequential tests, and handoff evidence.

The title slide contains only **Classifying Kidney Transplant Rejection from
Biopsy RNA**. State the comparative question aloud: how do the tested classifiers
differ in missed rejection and false positives when classifying any recorded
rejection versus no rejection in the public B-HOT dataset?

After explaining the biopsy, state the purpose: use an established molecular
application to assess what a more complex classifier contributes before further
validation, and build software that preserves the evaluated procedure. Restore
Banff's recognized role for validated biopsy transcript tests in defined settings
for antibody-mediated rejection. Explain that Zhang's source study already
compared model families and selected LASSO for similar accuracy with fewer
features. This project's contribution is an independent binary comparison with
explicit error analysis and tested software. Added diagnostic value from this
particular score needs direct evaluation.

## Content and time budget

Slides 1–12 retain their order and planned timings, totaling 11 minutes
25 seconds. The replacement section totals 8 minutes 35 seconds. Treat these
allocations as approximate pacing aids. Refine delivery through rehearsal rather
than treating a per-slide estimate as a deadline.

| Slides | Section | Planned allocation |
| --- | --- | ---: |
| 1–12 | Accepted question, context, methods, and validation results | 11:25 |
| 13 | Inspecting the analysis report, live | 0:45 |
| 14 | One public specimen through the service, live | 2:00 |
| 15 | Shared preparation and scoring | 1:10 |
| 16 | An interface other software can call | 1:10 |
| 17 | Checking the application against the analysis | 1:35 |
| 18 | Running and maintaining the application | 1:10 |
| 19 | What this project accomplished | 0:45 |
| | **Total, with questions afterward** | **20:00** |

| Slide | Subject | Evidence or visual |
| ---: | --- | --- |
| 1 | Classifying Kidney Transplant Rejection from Biopsy RNA | Title only |
| 2 | Transplant rejection and kidney biopsy | Definition labels and biopsy-evidence sub-bullets |
| 3 | Purpose of this project | Established application, the contribution of a more complex classifier and software that preserves the evaluated procedure |
| 4 | Clinical and research context | Banff's role for validated transcript tests, Zhang's model comparison and choice of LASSO, and why both errors matter |
| 5 | What the dataset contains | Linked analysis-table schemas, specimen counts, and the patient/referring-center separation qualification |
| 6 | Outcome: rejection versus no rejection | Binary mapping of the included diagnoses and exclusion qualification |
| 7 | The measurements used to build the features | Three bullets each explain the 758 model measurements and 12 housekeeping references |
| 8 | Normalization | Numbered calculation and a concrete example |
| 9 | Development and evaluation groups | Authors' discovery/validation division and the training/screening split; brief terminology clarification in the script |
| 10 | Model comparison | Constant, IFNG logistic regression, all-RNA logistic regression, and CatBoost; Approach and rationale column |
| 11 | Selecting the model and threshold | Recall and precision fractions, the screening rule, and a native table showing 157/174 detected by both models with five versus six false positives |
| 12 | Validation results | Preserved error chart, the eight-case CatBoost advantage and its uncertainty in narration, plus the 13-to-seven discovery-only selection counts |
| 13 | Inspecting the analysis report | Open the offline rendering of the preserved report and show how another analyst can inspect the evidence |
| 14 | One public specimen through the service | Show a valid public example, its versioned score and threshold, then the incomplete-file response |
| 15 | Shared preparation and scoring | Short source excerpt and editable explanation of the calculation shared by research and prediction |
| 16 | An interface other software can call | Concrete request/response example and the boundary between the application and calling software |
| 17 | Checking the application against the analysis | Saved all-specimen agreement check, a readable assertion excerpt, and consequential input failures |
| 18 | Running and maintaining the application | Documented setup, automated checks, tested local container, and the limits of existing deployment evidence |
| 19 | What this project accomplished | Observed CatBoost advantage, remaining uncertainty, working software, cross-validation as a next step and the untested clinical benefit |

The report stop demonstrates an inspectable deliverable. Do not repeat the
validation chart or add another results lecture. The application stop follows
one public specimen. Resume the slides afterward. Keep the complete
[Code Guide](CODE_GUIDE.html) available for questions, while presenting the
selected implementation content directly on slides.

## Required evidence

- Preserve the model labels, counts and explanatory sequence through slide 12,
  with the September 21 reframing described below. Use absolute counts and
  denominators alongside percentages. The 90% screening recall target was an
  experiment choice, and validation recall fell below it.
- Call the output a model score. Keep threshold selection separate from
  probability calibration. The all-RNA logistic regression comparison remains
  a credible simpler alternative. The report's uncertainty and follow-up
  evidence do not establish a clear overall winner.
- Render the preserved primary `REPORT.md` into the offline report view.
  Identify its source and retain links to the saved evidence. Do not rewrite
  the historical report or rerun models as part of a presentation revision.
- Demonstrate public screening specimen GSM6510425, then remove IFNG using
  the application's incomplete-file example. Show the model version,
  `20260915_shared:any_rejection:catboost_all_depth4`, and frozen threshold
  `0.8765880870219778`. The valid score is `0.27493421380277305`. An incomplete
  input yields an explanatory error and no score. This demonstration is not
  additional validation.
- Use source excerpts from the actual prediction and verification code.
  Explain how the same preprocessing code protects agreement between research
  and application behavior. Match the displayed API fields to the real response.
- Explain the recorded comparison across all 345 validation specimens: HTTP,
  command-line, and saved research outputs agreed within numerical tolerance,
  including reordered input columns, and the flags matched. This establishes
  software consistency rather than a new estimate of classifier performance.
- Date test and container evidence. Distinguish completed local checks from
  hosted checks on earlier revisions. A deployment guide is not a completed
  cloud deployment. No cloud deployment or new test run is implied by revising
  the slides.
- Describe personal contributions and AI assistance accurately. Present
  completed work as completed and proposed work as proposed. Avoid implying
  clinical deployment, patient benefit, or team experience from this project.
- Preserve the population qualification: the 1,395 specimens include 1,193
  transplant biopsies and 202 native-kidney controls. Public metadata do not
  identify controls individually. All specimens were processed at one laboratory,
  and patient/referring-center separation is not documented. Some difficult
  diagnosis categories were excluded. Do not claim all ambiguous biopsies were
  absent or that this project evaluated their clinical benefit.

## September 21 reframing

- Slides 1 and 2 introduce the established molecular application and the modeling
  choice. Keep the opening visual title unchanged.
- Slide 3 explains the purpose: assess what a more complex classifier contributes
  before further validation, and preserve the evaluated procedure in software.
- Slide 4 restores Banff's defined role for validated molecular tests and explains
  Zhang's comparison of model families and preference for LASSO. This binary
  comparison does not reproduce the published LASSO. Retain the reason both
  error types matter.
- Slide 10 keeps the model table and uses the comparative question in narration.
- Slide 11 retains the recall/precision definitions and shows why the fixed rule
  selected CatBoost: both detected 157 of 174 screening rejection cases, with
  five versus six false positives among 89 no-rejection specimens. The rule uses
  at least 90% recall, then the fewest false positives, with ROC-AUC breaking ties.
- Slide 12 retains the validation chart. State that CatBoost missed eight fewer
  rejection cases with eight false positives for each model. This adds evidence
  in its favor, while the paired recall-difference interval includes zero. Add
  the completed discovery-only follow-up: CatBoost selected 13 of 20 times and
  logistic seven. Those overlapping splits leave a dependable preference unsettled.
- Slide 19 returns to the purpose: evidence for the classifier choice and software
  that preserves the calculation. Propose cross-validation within discovery and
  identify added diagnostic value from this particular score as untested.

Slides 5–9 and 13–18 retain their visual content and narration. Slide 7's accepted
RNA/reference bullets and slide 9's terminology distinction remain. Historical
wording and study reviews remain evidence of their dates. The
[purpose note](references/PRESENTATION_PURPOSE_20260921.md) records the final
framing; the [earlier revision](references/PRESENTATION_REFRAMING_20260921.md)
records the model-choice counts. No experiments, thresholds or model artifacts change.

## Design and delivery checks

Give each slide one main purpose. Use ordinary dark-text bullets for parallel
points, numbered steps for calculations, and bold labels for definitions. Reserve
color for a consistent meaning. Group an explanation with its evidence. Keep
charts, tables, code text, and process diagrams editable. Enlarge the selected
code enough to read at presentation size and show only the lines needed to
explain the decision.

Map substantive script topics to visible support. Spoken elaboration and
transitions do not each need a slide cue. Put concise citations beside external
claims and full linked references in the HTML script. Keep PowerPoint notes
empty.

Verify the deck and PDF for clipping, readable labels, contrast, and consistent
values. Check the offline report and demonstration fallback. The fallback must
show the same software and model as the live example. Rehearse the report and
application transitions as part of the talk.

Complete at least two full timed rehearsals and one interruption/fallback
rehearsal. Aim to land at 20 minutes without rushing. Keep a short cut list for
delays rather than speaking faster. Record actual rehearsal times separately
from planned allocations.

## Material for questions

This revision has no backup slides. Keep the saved reports, Code Guide, source
reviews, and software verification records available for questions. They retain
the detailed uncertainty calculation, development-split follow-up, assay and
label details, reliability assessment, subtype analysis, and deployment limits.
Their removal from the deck does not remove or change the underlying work.
