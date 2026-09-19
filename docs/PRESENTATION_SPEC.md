# Twenty minute UNOS interview presentation

## Deliverable

Prepare a full 20-minute presentation about this project's question, analysis,
results, and software. Questions follow the presentation. Preserve the current
19 main slides and 8 backup slides for this revision. Give substantive topics
readable visual support without adding a cue for every spoken elaboration.

Deliver an editable `presentation/unos_kidney_biopsy.pptx`, a matching PDF backup,
a separate `presentation/speaking_script.html`, and the presentation source files.
All spoken text and delivery cues belong in the HTML file. **Do not use PowerPoint
notes.** This follows the user's September 18, 2026 delivery instruction.

The [current draft](../presentation/README.md) contains 19 main slides and 8 backup
slides, with a complete HTML speaking script planned for 20 minutes. The deck,
PDF, and static demonstration fallback are available. Actual timed rehearsals
remain pending; planned timing does not establish measured delivery time.

Follow [Presentation guide](PRESENTATION_GUIDE.md), whose design advice draws on
sources published from 2007 through 2014. The newer clinical-rationale sources
are documented in [Research context](RESEARCH_CONTEXT.md). Use the project's own
run outputs for every project result.

## Audience and purpose

Assume a mixed Product and Tech interview panel. Define the biopsy prediction task
before naming the algorithm. Explain enough transplant context for a technical
interviewer without presenting a clinical lecture. Show the candidate's choices,
what the models did, and how the result becomes usable software.
Define biopsy and RNA before explaining the model inputs. Keep the assay,
instrument, and panel terminology in the first backup slide.
Distinguish the RNA measurements from the recorded diagnosis the model predicts.
Use "specimen ID" for the identifier that matches a specimen to its source record.
Introduce "cohort" on slide 9 alongside the discovery and validation groups.

The title slide contains only **Classifying Kidney Transplant Rejection from
Biopsy RNA**, following the user's September 19, 2026 selection. State the research
question aloud. Results come after the audience has enough context to understand
them.

Immediately after the biopsy explanation, explain the intended use: a molecular
second opinion could give specialists additional evidence when a transplant
biopsy is uncertain or conflicts with other findings. Histology examines tissue
appearance, while RNA measurements describe gene activity. Current Banff guidance
and B-HOT research support investigating this role.

The project develops and evaluates an early research prototype for that purpose.
Its measurements classify recorded rejection with a measurable error tradeoff,
and its shared pipeline supports reproducible scoring of further specimens.
Testing added benefit for uncertain biopsies is a possible extension requiring
clinical collaborators. Present this qualification alongside the intended use,
then frame later suggestions as hypothetical extensions of this personal project.
Do not claim ambiguous specimens were absent from training without
evidence. The UNOS kidney-photo research connection belongs in a backup
slide as an example of research toward supporting expert assessment in a
different task.

## Content and time budget

The outline puts the purpose immediately after the biopsy explanation, then
presents supporting evidence, the dataset, the outcome, and the measurements.
Keep detailed assay terminology in the appendix. Use the
following approximate section allocations to plan a full 20-minute talk. The
HTML's per-slide and cumulative times are rough pacing aids, not measured rehearsal
times or deadlines for each slide. Refine pacing from actual delivery rather than
laboriously optimizing estimates.

| Slides | Section | Approximate time |
| --- | --- | ---: |
| 1–4 | Question, transplant context, possible use, and supporting research | 3¾ minutes |
| 5–8 | Dataset, outcome, measurements, and normalization | 3¾ minutes |
| 9–11 | Study groups, models, and threshold | 2¾ minutes |
| 12–14 | Validation errors and comparison uncertainty | 4¼ minutes |
| 15–17 | Prediction software, demonstration, and checks | 3¾ minutes |
| 18–19 | Possible extensions and project accomplishments | 1¾ minutes |
| | **Total, with questions afterward** | **20 minutes** |

| Slide | Subject | Evidence or visual |
| ---: | --- | --- |
| 1 | Classifying Kidney Transplant Rejection from Biopsy RNA | Title only |
| 2 | Transplant rejection and kidney biopsy | Bold definition labels and indented biopsy-evidence sub-bullets, with consistent gaps between the visible text blocks |
| 3 | Possible Use: Molecular Second Opinion for Ambiguous Biopsies | Matching boxes labelled Hypothetical Example, before and after a possible molecular assessment |
| 4 | Evidence for a molecular second opinion | Banff guidance, B-HOT research, and why unnecessary rejection treatment can worsen infection; keep the project's scope visible |
| 5 | What the dataset contains | Two analysis-table schemas linked by specimen ID; matching bullets at the same font size for the specimen counts and the patient/referring-center separation note directly underneath, without an asterisk |
| 6 | Outcome: rejection versus no rejection | Colored summary above the diagnosis table; binary mapping of the included categories and a short exclusion note |
| 7 | The measurements used to build the features | 758 model measurements and 12 housekeeping references used to adjust for differences in RNA quantity |
| 8 | Normalization | Compact numbered calculation and example for each of the 758 counts |
| 9 | Development and evaluation groups | Authors' discovery/validation division and this project's training/screening split |
| 10 | Model comparison | Constant, IFNG, logistic regression, and CatBoost; each produces a rejection score |
| 11 | Threshold selection | Recall and precision as stacked fractions with words in the numerator and denominator, then the screening selection rule |
| 12 | Validation results | False negatives and false positives on the same rows, with class denominators |
| 13 | Errors by recorded diagnosis | False negatives within each rejection group |
| 14 | Comparison uncertainty | Paired comparison and discovery-only stability follow-up |
| 15 | Prediction service and demonstration | Transition into software, with input checks, shared preprocessing, model and response |
| 16 | Working demonstration | Valid specimen and incomplete-file response |
| 17 | Software checks | Consequential tests and current deployment evidence |
| 18 | Possible next steps | Hypothetical extensions of a personal project: another dataset and a possible study with clinical collaborators |
| 19 | What this project accomplished | Separate model-comparison and service/demo sections; error percentages with counts and denominators; no next-step bullet |

Give the central result and its tradeoff enough time after explaining the task.
A methods nuance should occupy only the space needed to understand the result.
Backup slides 20–27 support questions and sit outside this timing budget. Slide 20
contains the assay explanation moved from the main talk.

## Required evidence

- Use absolute counts and denominators alongside percentages. Show recall as
  recorded rejection cases detected divided by all recorded rejection cases,
  and precision as flags with recorded rejection divided by all positive flags.
  Use stacked word fractions on slide 11. Explain false negatives
  as missed cases and false positives as incorrect flags. The selection procedure
  requires at least 90% screening recall, then minimizes false positives. This
  second criterion maximizes specificity, not precision. State that the 90% target
  is an experiment choice and that validation recall fell below it.
- Explain IFNG as one immune-related measurement used for a simple benchmark.
  The source study associates it with T-cell-mediated rejection, but this project
  did not establish it as the best individual predictor. Keep the probability
  interpretation separate from threshold choice and use "model score" throughout.
- Include the regularized multivariable comparison. Do not make the talk depend on
  a complicated model winning.
- Distinguish the binary benchmark, four-class follow-up, and original study.
  Do not compare accuracy percentages across different prediction tasks.
- Show the model version and threshold in the demonstration. Use only public
  study examples with no invented clinical history.
- Explain the intended clinical role and the measured research contribution in
  plain language. Distinguish external evidence from this project's results.
  Keep extra methodological detail and secondary targets in backup slides.
- Describe work actually completed, including the candidate's decisions and
  appropriate disclosure of AI assistance. Present proposed work as proposed.
- In the script for slide 5, distinguish the two assembled analysis tables from
  the two public downloads, one of which contains individual count files. Both
  author study groups contribute to the 1,395 specimens, as explained on slide 9.
  The full article reports 202 native-kidney controls, so this evaluation is not
  restricted to transplant biopsies. Public metadata do not map those controls
  to individual records. The study does not document patient or referring-center
  separation, and all specimens were processed at one laboratory.
- Keep the paired clinical example explicitly hypothetical. The study excluded
  some difficult diagnostic categories, including borderline acute T-cell-mediated
  rejection. Explain the full exclusions in backup material, without claiming that
  all ambiguous biopsies were excluded. Do not assume false negatives are always
  more consequential: the article discusses harmful additional immunosuppression
  if infection is mistaken for rejection.

## Design and delivery checks

Give each slide one main purpose. Use ordinary dark-text bullets for parallel
points, numbered steps for calculations, and bold labels for definitions. Reserve
color for a consistent meaning, including the unbulleted summary lines requested
for the dataset, outcome, measurements, and normalization. Group each explanation with the count, example,
table, or diagram it explains. Do not add unrelated statements at the bottom.

Use real charts and diagrams that explain meaningful relationships or processes.
Keep the useful diagrams on slides 9 and 15. Slide 2 needs definition bullets and
sub-bullets. Slide 3 needs two matching hypothetical-example boxes. Slide 5 needs
table schemas. The assay explanation on backup slide 20 uses bullets. Avoid generic
stock imagery, decorative medical imagery, dense dashboard cards, and lists of
tools that take space away from evidence. Keep charts and required tables editable.
Put concise citations beside externally sourced claims and full linked references
in the HTML speaking script. Omit footers about the location of those full links.
Do not repeat source citations already named beside the evidence. Keep PowerPoint
notes empty.

Map each substantive topic in the script to visible support. Use readable labels,
brief bullets, examples, and evidence rather than copying paragraphs. Split a
script section across slides when its topics need different visuals. Keep the
terms and sequence aligned. Spoken elaboration, asides, and transitions do not
each need their own cue. Keep delivery instructions sparse and practical.
Use plain topic titles for setup slides and the requested "Validation results"
title for slide 12. Use supported findings where useful on other result slides.
A definition label should be visually
distinct from its explanation.

Verify the exported deck and PDF for readable labels, clipping, contrast, and
consistent numeric values. Keep a static screenshot or short local recording of
the demonstration so a network or application failure does not interrupt the talk.
The fallback must show the same software and model as the live example.

Rehearse aloud with the demonstration included. Complete at least two full timed
runs and one interruption/fallback rehearsal. Aim to land at 20 minutes without
rushing the results. Keep a short cut list for unexpected delays rather than
shrinking every slide or speaking faster.

## Backup material

Prepare concise answers with supporting slides for label mapping, preprocessing,
the full model comparison, threshold choice, calibration, secondary rejection
components, study limitations, testing, deployment, and what would change at a
larger data volume. Include the UNOS kidney-photo research connection with its
source and the difference in clinical task. Backups do not count toward the
planned 20 minutes.
