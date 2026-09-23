# Twenty minute UNOS interview presentation

Current revision: September 23, 2026. The requested structure is **slideshow,
one continuous browser demonstration, then slideshow**. Deliver 14 main slides
without backup slides. The full talk is planned for 20 minutes; questions follow.

## Deliverables and audience

Deliver an editable `presentation/unos_kidney_biopsy.pptx`, matching PDF,
`presentation/speaking_script.html`, and `presentation/engineering_demo.html`.
Keep the complete primary report and captured-application fallback available.
All spoken text, delivery cues and timings belong in the speaking script.
**Keep PowerPoint notes empty.**

The panel includes a data scientist, two biostatisticians and a manager with a
master's in public health. Explain the work through concrete questions: why this
distinction matters, what the errors show, how someone can use the model, and
whether the software preserves the evaluated calculation. The
[job requirements](JOB_REQUIREMENTS.md) guide the selection of evidence.

The clinical motivation is that whether rejection is present can affect decisions
about further treatment to suppress the immune system. A molecular score could
provide additional evidence during that assessment. Give the model comparison
and software engineering equal prominence, as recorded in the
[research context](RESEARCH_CONTEXT.md#established-application-and-project-purpose).

## Sequence and time budget

| Segment | Content | Time |
| --- | --- | ---: |
| Slides 1–12 | Context, question, methods and results | 11:25 |
| Slide 13 | Software Engineering Demo transition | 0:15 |
| Browser stop 1 | Inspect saved evidence | 1:15 |
| Browser stop 2 | Score a public specimen | 2:15 |
| Browser stop 3 | Shared calculation, API, verification and handoff | 4:00 |
| Slide 14 | Completed model comparison and software engineering | 0:50 |
| **Total** | **Questions afterward** | **20:00** |

These are planned allocations. The presenter reports rehearsing as of September 23; measured durations have not been supplied.

| Slide | Subject and required content |
| ---: | --- |
| 1 | Classifying Kidney Transplant Rejection from Biopsy RNA. Title only. |
| 2 | Rejection, kidney biopsy, histology and molecular measurements, with the user's wording suited to reading aloud. |
| 3 | Treatment-related motivation, with both error consequences explained aloud; binary question against recorded diagnoses; equally prominent software-engineering aim. |
| 4 | Banff's defined role for validated transcript tests; Zhang's regression/boosting comparison and choice of LASSO; a Biopsy and treatment row with KDIGO recommendation 6.1 and its exception for substantial treatment delay. |
| 5 | Linked count/metadata tables, specimen totals, native-kidney controls and undocumented patient/referring-center separation. |
| 6 | Any recorded rejection versus no rejection, with examples of excluded diagnoses explained in the script. |
| 7 | The 758 model measurements and 12 housekeeping references. |
| 8 | Per-specimen normalization, with the actual IFNG example. |
| 9 | Author discovery/validation cohorts and the 787/263 training/screening split. |
| 10 | Constant, IFNG, logistic regression and CatBoost, with concise rationale. |
| 11 | Recall and precision, threshold selection and the recorded screening counts. |
| 12 | Editable validation error chart with teal Incorrect flags before orange Missed cases in the legend, matching the bars; discovery selection count highlighted in the deck's teal, with the 20-repetition design explained aloud. |
| 13 | Title: Software Engineering Demo. Retain Reports, application and scoring service as the subtitle. No bullets. Introduce the browser stops aloud. |
| 14 | Completed model comparison and software engineering. Remove the next-steps text from both the slide and spoken closing. |

Slides 1–12 retain their established order and time allocations. Return once to
PowerPoint for slide 14. Detailed methods and likely answers stay in the reports.

### Specific wording and layout

- Slide 2 uses ordinary definition bullets with biopsy-evidence sub-bullets and
  even spacing. Histology: “A microscopic examination that reveals injury and
  inflammation, which can support a rejection diagnosis.” Molecular measurements:
  “Counts of selected RNA types that reflect gene activity in the mix of cells
  in the tissue.” Explain model-input transformation later.
- Slide 3 gives the two aims equal visual weight. Explain both potential harms
  aloud: missed rejection can leave kidney injury untreated, while unnecessary
  immunosuppression can worsen an infection. These are potential consequences,
  not measured outcomes of this classifier.
- Slide 4's treatment row says: “KDIGO recommends biopsy before treating acute
  rejection, unless waiting would substantially delay treatment.” Keep the
  exception in the script. Leave the project's binary question on slide 3.
- Slide 5 keeps the two table schemas joined by specimen ID. Explain their
  assembly from public files in narration, without a redundant on-slide caption.
- Slide 7 groups three bullets under each count. Under 758: selected human and
  viral RNAs; signals reflect gene activity and cell mixture; normalized values
  become inputs. Under 12: relatively stable reference RNAs; adjustment for
  overall measurable RNA input; normalization followed by removal from predictors.
  Slide 8 shows the numbered calculation without repeating those explanations.
- Slide 10 uses “Approach and rationale.” CatBoost can represent nonlinear
  patterns and interactions; shallow trees limit complexity without guaranteeing
  against overfitting. Numerical features are supported without categorical inputs.
  Distinguish IFNG-only from all-RNA logistic regression explicitly.
- Slide 11 uses stacked word fractions. Both numerators say “Correctly flagged
  rejection cases”; recall divides by “All cases diagnosed as rejection” and
  precision by “All rejection flags.” Explain denominators first. Removing a
  false positive reduces the precision denominator; it does not add a true positive.
- Slide 12 retains the spoken IFNG comparison before the constant baseline, but
  omits the extra CatBoost-versus-IFNG bullet. Use teal, not purple, for the 13/7
  emphasis: “Follow-up screening selections across 20 discovery splits: CatBoost 13,
  logistic 7.” Keep the legend order and error colors specified above.
- Slide 14 and its narration close on completed analysis and software, followed
  by acknowledgments. Deferred research remains in the linked reports.

## Browser demonstration

Use one self-contained HTML page with three main stops. The separate speaking
script supplies the complete narration and click instructions for each stop.
Browser stops are not numbered as slide pages.

1. **Evidence:** Inspect errors by recorded diagnosis, then the saved discovery
   follow-up. Show the source records behind the 13/7 count, with all 20 selections
   available to expand. Link the complete primary and follow-up reports. Avoid
   repeating slide 12's full model comparison as another results lecture.
2. **Application:** The tab shows a selected-column preview of the actual input
   CSV, the launch command and one link to the existing research app in a separate
   tab. The app demonstrates public screening specimen GSM6510425 and the
   incomplete example with IFNG removed. Scores, thresholds and flags appear in
   the app rather than a duplicate interface in the engineering page. Separate
   captured screenshots remain available for offline delivery.
3. **Engineering:** Show actual source excerpts for shared preparation and
   prediction, an actual API request/response, the saved 345-specimen agreement
   check and important failure cases. Finish with the run instructions, automated
   checks and dated local-container evidence. Full documentation remains available
   inside the reference library.

The launcher serves the page alongside the unchanged FastAPI research app on
localhost. It must not refit models or silently substitute another model for the
demonstrated one. The integration check compares the served model version and threshold with
the saved response. The saved API response was generated by the same application
and frozen model. The source JSON and report hashes identify the displayed evidence.

### Engineering-page wording and structure

The page title is **Software Engineering**. It has no speaking-script link.
Explanations use named subjects and declarative sentences. Each view identifies
its question, population and method before presenting results. The repeated-split
view explains the narrow original screening advantage, then the two random,
diagnosis-stratified splitting steps, all three discovery groups and specimen reuse.
Identify the smaller training set and revised candidate settings, fixed across
repetitions. The 13/7 screening selection table supplies the main result. Place
assessment errors in an expandable supporting section and state that they did not
determine those selections. Keep the revised tab text no longer than its prior version.
Engineering sections explain the shared calculation, programmatic access,
verification and setup before showing their supporting code and records.

## Evidence and scope

- The main comparison uses the same 345 technical-validation specimens. CatBoost
  missed 25/169 rejection cases and incorrectly flagged 8/176 no-rejection cases;
  logistic missed 33 with 8 incorrect flags. The paired-bootstrap 95% interval
  for the recall difference is approximately −0.01 to +9.74 percentage points,
  including zero. The discovery follow-up selected CatBoost 13 times and logistic 7.
- Each of the 20 follow-up repetitions partitions discovery into 630 training,
  210 screening and 210 held-out assessment specimens. The author validation cohort
  is unused. Repetitions overlap and are not independent validation trials.
- The screening rule requires at least 90% recall, then minimizes false positives
  with ROC-AUC as a tie-breaker. Both main screening models detected 157/174;
  CatBoost produced five false positives versus six for logistic among 89 cases.
  Validation recall fell below the experimental target.
- Call the output a model score. Threshold selection and probability calibration
  are separate questions. Do not compare this binary accuracy directly with
  Zhang's four-class accuracy or suggest the binary endpoint is itself new.
- Native controls are part of the evaluated population: 1,193 transplant biopsies
  and 202 native-kidney controls overall; 334 and 11 in validation. Public metadata
  lack specimen-level native status and patient/referring-center identifiers.
  Separation between cohorts is not documented, which does not prove overlap.
- The source excluded borderline acute T-cell-mediated rejection, chronic inactive
  antibody-mediated rejection and some chronic active T-cell-mediated rejection.
  Name the first two in the script; their exclusion counts are not reported.
  Assay QC exclusions are separate and cannot supply those counts. The
  [source-study review](references/STUDY_AUDIT_20260919.md) gives exact categories
  and pages. Do not claim that all difficult cases were excluded.
- KDIGO recommendation 6.1 supports the biopsy/treatment connection. Retain the
  exception for substantial treatment delay on slide 4 and in its script. Explain
  the two error consequences in slide 3 narration.
  It does not establish the clinical usefulness of this model. Banff and Zhang
  provide distinct context and remain on slide 4.
- The demonstration uses the frozen Mac run selected in
  `presentation/source/demo_config.json`. The
  [presentation README](../presentation/README.md#frozen-run-and-evidence) records
  its version, threshold, example and the older desktop evidence still included.
  This demonstration is not a new classifier evaluation.
- The saved HTTP verification covers all 345 specimens, including reordered
  measurement columns, with matching flags and scores within 1e-12 across routes.
  Date the record. Distinguish software consistency from classifier performance,
  and earlier hosted CI from local research-container checks. Cloud deployment
  remains future work.

## Design, verification and rehearsal

Follow the dated sources and audience guidance in [Presentation guide](PRESENTATION_GUIDE.md).
Keep one main point per slide, readable native charts/tables and the established
palette. Use orange for missed cases and teal for incorrect flags. General teal
emphasis is already part of the design; do not introduce purple for the split result.
Use the same terminology in the deck, browser page and script.

Inspect all final slide renders and the matching PDF. Check browser navigation,
source dialogs, the real valid/invalid example, saved-response fallback and return
to the closing slide. Check that retained slides and chart values are preserved.
Keep temporary validation records under the private build directory.

Complete two full timed rehearsals and one interruption/fallback rehearsal.
Rehearsal must include both screen-share transitions. The script contains its
planned timing and a way to record measured duration. Detailed methods, sources
and likely question answers remain in the reports and reference library.

Current requirements are consolidated here. Earlier presentation revisions
remain in Git history; source reviews remain under `docs/references/`.
