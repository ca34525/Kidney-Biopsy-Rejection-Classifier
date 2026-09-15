# Twenty minute UNOS interview presentation

## Deliverable

Prepare a full 20-minute presentation about this project's question, analysis,
results, and software. Questions follow the presentation. Plan approximately
12 main slides, with backup slides for detailed methods and questions. Slide count
is a planning choice; preserve the 20-minute content budget when revising it.

Deliver an editable `presentation/unos_kidney_biopsy.pptx`, a matching PDF backup,
speaker notes, and the presentation source files. These are planned deliverables,
not files already produced by this specification.

Follow [Presentation guide](PRESENTATION_GUIDE.md), which draws on external sources
published from 2007 through 2014. Use the project's own run outputs for every result.

## Audience and purpose

Assume a mixed Product and Tech interview panel. Define the biopsy prediction task
before naming the algorithm. Explain enough transplant context for a technical
interviewer without presenting a clinical lecture. Show the candidate's choices,
what the models did, and how the result becomes usable software.

The main point should emerge from the actual results. A possible structure is:
several molecular measurements can help classify recorded rejection, the chosen
threshold has a measurable error tradeoff, and a shared pipeline makes the result
reproducible and usable in a research application. Revise that claim if the results
support a different conclusion.

## Content and time budget

| Slide | Subject | Evidence or visual | Minutes |
| ---: | --- | --- | ---: |
| 1 | Project question and concise result | Plain title and one supported finding | 1:00 |
| 2 | The research user's task | Biopsy, assay, and proposed research use | 1:30 |
| 3 | What one observation contains | One specimen, measured inputs, recorded label | 1:30 |
| 4 | Data preparation | Source files, matching, normalization, resulting matrix | 2:00 |
| 5 | A fair comparison | Cohort diagram, simple baselines, screening rule | 2:00 |
| 6 | Model results | Readable comparison using this project's evaluation | 2:00 |
| 7 | What the errors mean | Missed rejection and false flags at the stated thresholds | 2:00 |
| 8 | One finding from error review | A concrete pattern or a useful negative result | 1:30 |
| 9 | How the software works | Input, shared preprocessing, model, response | 1:30 |
| 10 | Working demonstration | Valid sample plus clear invalid-input response | 2:00 |
| 11 | Reliability and next improvement | One meaningful test, deployment status, main remaining gap | 1:30 |
| 12 | Conclusion and contribution | What was learned, what was built, next useful step | 1:30 |
| | **Total speaking time** | **Questions afterward** | **20:00** |

Use an early supported result to orient the audience, then explain why it is
credible. Give the central result and its tradeoff enough time. A methods nuance
should occupy only the space needed to understand the result.

## Required evidence

- Use absolute counts and denominators alongside percentages. Explain sensitivity
  and specificity through missed rejection and false flags before using the terms.
- Include the regularized multivariable comparison. Do not make the talk depend on
  a complicated model winning.
- Distinguish the binary project target from the original study's four-class task.
  Do not compare their accuracy percentages as if they measured the same task.
- Show the model version and threshold in the demonstration. Use only public
  study examples with no invented clinical history.
- Explain current use and the main limitation in plain language. Keep extra
  methodological detail and secondary targets in backup slides.
- Describe work actually completed, including the candidate's decisions and
  appropriate disclosure of AI assistance. Present proposed work as proposed.

## Design and delivery checks

Give each slide one main purpose. Use real charts and clear diagrams. Avoid generic
stock imagery, decorative medical imagery, dense dashboard cards, and lists of
tools that take space away from evidence. Keep charts and required tables editable.
Put citations beside externally sourced claims or in the speaker notes as appropriate.

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
larger data volume. Backups do not count toward the planned 20 minutes.
