# Twenty minute UNOS interview presentation

## Deliverable

Prepare a full 20-minute presentation about this project's question, analysis,
results, and software. Questions follow the presentation. Use enough slides to
give each spoken topic a readable visual cue. Slide count is a planning choice;
preserve the 20-minute content budget when revising it.

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

The title slide introduces the topic and research question. It does not introduce
error counts, a winning algorithm, or an interview-project tagline. Results come
after the audience has enough context to understand them.

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
the next study. The UNOS kidney-photo research connection belongs in a backup
slide as an example of research toward supporting expert assessment in a
different task.

## Content and time budget

The current outline puts the purpose immediately after the biopsy explanation,
then separates supporting evidence, measurement roles, and model selection so
each has matching slide content. The HTML script gives the same
slide-by-slide and cumulative timing. These are planned durations, not measured
rehearsal times.

| Slide | Subject | Evidence or visual | Minutes |
| ---: | --- | --- | ---: |
| 1 | Research question | Topic and question | 0:20 |
| 2 | Biopsy and rejection | Tissue sample, transplant context, recorded diagnosis | 0:55 |
| 3 | Molecular support for uncertain biopsies | Additional evidence for specialist review of existing tissue | 1:00 |
| 4 | Evidence for a molecular second opinion | Banff guidance and B-HOT research, with their scope | 0:55 |
| 5 | Recorded diagnoses | Four diagnoses and the binary rejection label | 0:40 |
| 6 | RNA and the assay | Molecules in tissue and how the assay measures them | 0:55 |
| 7 | Measurement roles | 758 model inputs and 12 housekeeping reference measurements | 0:45 |
| 8 | One observation | Specimen ID, counts, and diagnosis kept separate | 0:55 |
| 9 | Normalization | Raw counts, within-specimen reference, transformed inputs | 1:10 |
| 10 | Development and evaluation groups | Authors' cohorts and discovery training/screening split | 1:00 |
| 11 | Model comparison | Constant, IFNG, logistic regression, and CatBoost | 0:50 |
| 12 | Threshold selection | Discovery screening rule and the error tradeoff | 0:55 |
| 13 | Evaluation errors | Same-row comparison with class denominators | 1:50 |
| 14 | Errors by recorded diagnosis | Missed rejection within each rejection group | 1:15 |
| 15 | Comparison uncertainty | Paired comparison and discovery-only stability follow-up | 1:00 |
| 16 | Prediction software | Input checks, shared preprocessing, model, response | 1:00 |
| 17 | Working demonstration | Valid specimen and incomplete-file response | 2:00 |
| 18 | Software checks | Consequential tests and current deployment evidence | 0:50 |
| 19 | Next evidence for a molecular second opinion | New cohort, laboratory checks, and a direct test of added benefit | 1:00 |
| 20 | Conclusion | Intended use, measured contribution, next step | 0:45 |
| | **Total speaking time** | **Questions afterward** | **20:00** |

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

## Design and delivery checks

Give each slide one main purpose. Use real charts and clear diagrams. Avoid generic
stock imagery, decorative medical imagery, dense dashboard cards, and lists of
tools that take space away from evidence. Keep charts and required tables editable.
Put concise citations beside externally sourced claims and full linked references
in the HTML speaking script. Omit footers about the location of those full links.
Keep PowerPoint notes empty.

Map each substantive topic in the script to an on-slide cue. Use readable labels,
brief bullets, examples, and evidence rather than copying paragraphs. Split a
script section across slides when its topics need different visuals. Keep the
terms, sequence, and timing aligned. Use plain topic titles for setup slides and
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
