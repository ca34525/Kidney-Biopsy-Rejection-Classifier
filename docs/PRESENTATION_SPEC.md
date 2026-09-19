# Twenty minute UNOS interview presentation

## Deliverable

Prepare a full 20-minute presentation about this project's question, analysis,
results, and software. Questions follow the presentation. Preserve the current
20 main slides and 7 backup slides for this revision. Give substantive topics
readable visual support without adding a cue for every spoken elaboration.

Deliver an editable `presentation/unos_kidney_biopsy.pptx`, a matching PDF backup,
a separate `presentation/speaking_script.html`, and the presentation source files.
All spoken text and delivery cues belong in the HTML file. **Do not use PowerPoint
notes.** This follows the user's September 18, 2026 delivery instruction.

The [current draft](../presentation/README.md) contains 20 main slides and 7 backup
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
Define biopsy, RNA, assay, and panel before using them to explain the model inputs.
Distinguish the RNA measurements from the recorded diagnosis the model predicts.
Use "specimen ID" for the identifier that matches a specimen to its source record.
Introduce "cohort" on slide 10 alongside the discovery and validation groups.

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
Testing added benefit for uncertain biopsies is the next research step. Present
this qualification alongside the intended use, then return to it when explaining
the next study. Do not claim ambiguous specimens were absent from training without
evidence. The UNOS kidney-photo research connection belongs in a backup
slide as an example of research toward supporting expert assessment in a
different task.

## Content and time budget

The outline puts the purpose immediately after the biopsy explanation, then
separates supporting evidence, measurement roles, and model selection. Use the
following approximate section allocations to plan a full 20-minute talk. The
HTML's per-slide and cumulative times are rough pacing aids, not measured rehearsal
times or deadlines for each slide. Refine pacing from actual delivery rather than
laboriously optimizing estimates.

| Slides | Section | Approximate time |
| --- | --- | ---: |
| 1–4 | Question, transplant context, possible use, and supporting research | 3 minutes |
| 5–7 | Recorded diagnoses, RNA assay, and measurement roles | 2½ minutes |
| 8–12 | Data tables, normalization, study groups, models, and threshold | 5 minutes |
| 13–15 | Evaluation errors and comparison uncertainty | 4 minutes |
| 16–18 | Prediction software, demonstration, and checks | 4 minutes |
| 19–20 | Further evidence and conclusion | 1½ minutes |
| | **Total, with questions afterward** | **20 minutes** |

| Slide | Subject | Evidence or visual |
| ---: | --- | --- |
| 1 | Classifying Kidney Transplant Rejection from Biopsy RNA | Title only |
| 2 | Transplant rejection and kidney biopsy | Two context bullets, with the diagram directly under its evidence label |
| 3 | Possible Use: Molecular Second Opinion for Ambiguous Biopsies | Full-sentence bullets and the proposed-use diagram |
| 4 | Evidence for a molecular second opinion | Banff guidance and B-HOT research, concise scope qualification, sources beside evidence |
| 5 | Recorded diagnoses | Four diagnoses and the binary rejection label |
| 6 | Measuring biopsy RNA | Bullets explaining RNA, NanoString nCounter, B-HOT, and an example |
| 7 | Measurement roles | 758 target counts and 12 housekeeping reference counts, with explanations grouped under each |
| 8 | What the dataset contains | Two condensed analysis-table schemas linked one-to-one by specimen ID |
| 9 | Normalization | Compact numbered calculation and example for each of the 758 target counts |
| 10 | Development and evaluation groups | Authors' discovery/validation division, then this project's training/screening split |
| 11 | Model comparison | Constant, IFNG, logistic regression, and CatBoost |
| 12 | Threshold selection | Discovery screening rule and the error tradeoff |
| 13 | Evaluation errors | Same-row comparison with class denominators |
| 14 | Errors by recorded diagnosis | Missed rejection within each rejection group |
| 15 | Comparison uncertainty | Paired comparison and discovery-only stability follow-up |
| 16 | Prediction software | Input checks, shared preprocessing, model, response |
| 17 | Working demonstration | Valid specimen and incomplete-file response |
| 18 | Software checks | Consequential tests and current deployment evidence |
| 19 | Next evidence for a molecular second opinion | New cohort, laboratory checks, and a direct test of added benefit |
| 20 | Conclusion | Intended use, measured contribution, next step |

Give the central result and its tradeoff enough time after explaining the task.
A methods nuance should occupy only the space needed to understand the result.
Backup slides 21–27 support questions and sit outside this timing budget.

## Required evidence

- Use absolute counts and denominators alongside percentages. Explain sensitivity
  and specificity through missed rejection and false flags before using the terms.
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
- On slide 8, distinguish the two assembled analysis tables from the two public
  downloads, one of which contains individual count files. The shared specimen
  key does not establish the number of independent patients. Both author study
  groups contribute to the 1,395 specimens, as explained on slide 10.

## Design and delivery checks

Give each slide one main purpose. Use ordinary dark-text bullets for parallel
points, numbered steps for calculations, and bold labels for definitions. Reserve
color for a consistent meaning. Group each explanation with the count, example,
table, or diagram it explains. Do not add unrelated statements at the bottom.

Use real charts and diagrams that explain meaningful relationships or processes.
Keep the useful diagrams on slides 2, 3, 10, and 16. Slide 6 needs bullets rather
than a flowchart; slide 8 needs table schemas. Avoid generic
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
Use plain topic titles for setup slides and
supported findings for result slides. A definition label should be visually
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
