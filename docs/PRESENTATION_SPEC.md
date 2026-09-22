# Twenty minute UNOS interview presentation

Current revision: September 22, 2026. The requested structure is **slideshow,
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
[purpose note](references/PRACTICAL_PURPOSE_20260922.md).

## Sequence and time budget

| Segment | Content | Time |
| --- | --- | ---: |
| Slides 1–12 | Context, question, methods and results | 11:25 |
| Slide 13 | Software engineering transition | 0:15 |
| Browser stop 1 | Inspect saved evidence | 1:15 |
| Browser stop 2 | Score a public specimen | 2:15 |
| Browser stop 3 | Shared calculation, API, verification and handoff | 4:00 |
| Slide 14 | Completed work and next research question | 0:50 |
| **Total** | **Questions afterward** | **20:00** |

These are planned allocations. Actual timed rehearsals remain pending.

| Slide | Subject and required content |
| ---: | --- |
| 1 | Classifying Kidney Transplant Rejection from Biopsy RNA. Title only. |
| 2 | Rejection, kidney biopsy, histology and molecular measurements, with the user's wording suited to reading aloud. |
| 3 | Treatment-related motivation; binary question against recorded diagnoses; equally prominent software-engineering aim. |
| 4 | Banff's defined role for validated transcript tests; Zhang's regression/boosting comparison and choice of LASSO; biopsy findings and treatment through KDIGO, followed by both error consequences. |
| 5 | Linked count/metadata tables, specimen totals, native-kidney controls and undocumented patient/referring-center separation. |
| 6 | Any recorded rejection versus no rejection, with examples of excluded diagnoses explained in the script. |
| 7 | The 758 model measurements and 12 housekeeping references. |
| 8 | Per-specimen normalization, with the actual IFNG example. |
| 9 | Author discovery/validation cohorts and the 787/263 training/screening split. |
| 10 | Constant, IFNG, logistic regression and CatBoost, with concise rationale. |
| 11 | Recall and precision, threshold selection and the recorded screening counts. |
| 12 | Editable validation error chart; discovery selection count highlighted in the deck's teal, with the 20-repetition design explained aloud. |
| 13 | Software engineering transition: inspect evidence, score a specimen, trace and check the calculation. |
| 14 | Model comparison, software engineering and the next research question. |

Slides 1–12 retain their established order and time allocations. Replace the
former technical slides 13–18 with browser material. Return once to PowerPoint
for slide 14; do not keep alternate technical slides or backups in the deck.

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
view explains the two random, diagnosis-stratified splitting steps, all three
discovery groups and reuse across repetitions before the 13/7 selection table.
The later error comparison explicitly concerns discovery assessment specimens.
Engineering sections explain the shared calculation, programmatic access,
verification and setup before showing their supporting code and records.

## Evidence and scope

- The main comparison uses the same 345 technical-validation specimens. CatBoost
  missed 25/169 rejection cases and incorrectly flagged 8/176 no-rejection cases;
  logistic missed 33 with 8 incorrect flags. The paired recall-difference interval
  includes zero. The discovery follow-up selected CatBoost 13 times and logistic 7.
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
  The diagnostic exclusion counts are not reported. Assay QC exclusions are a
  separate step and cannot supply those counts.
- KDIGO recommendation 6.1 supports the biopsy/treatment connection. In the script,
  retain the exception when waiting for biopsy would substantially delay treatment.
  It does not establish the clinical usefulness of this model. Banff and Zhang
  provide distinct context and remain on slide 4.
- The demonstrated model version is `20260915_shared:any_rejection:catboost_all_depth4`.
  Its threshold is `0.8765880870219778`; the public example score is
  `0.27493421380277305`. This is a demonstration, not new classifier validation.
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

The [engineering revision note](references/ENGINEERING_DEMO_20260922.md) records
the implemented change. Earlier dated notes and the archived 19-slide deck
preserve history; they do not describe the current sequence.
