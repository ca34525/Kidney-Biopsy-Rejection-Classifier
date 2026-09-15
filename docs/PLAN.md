# One week implementation plan

The exact interview date is unconfirmed. Treat the days below as working days
relative to the start, with the final day reserved for delivery practice. Protect
presentation time if implementation takes longer than expected.

| Day | Main work | Concrete finish |
| --- | --- | --- |
| 1 | Establish the independent project and rerun the starting analysis | Local raw data, verified sources, local environment, freshly trained models and results |
| 2 | Complete the important comparisons and error review | Constant, IFNG, multivariable logistic, and selected-model comparison; practical error counts; central plots |
| 3 | Extract shared preprocessing and prediction | A repeatable command-line prediction path, model metadata, meaningful input and consistency tests |
| 4 | Build the small API and demonstration page | Valid and invalid requests work through the same prediction code |
| 5 | Check packaging and prepare the first complete talk | Local container and CI; cloud attempt if access permits; all main slides drafted |
| 6 | Refine the presentation using actual results | Editable deck, notes, PDF, demo fallback, first complete timed rehearsal |
| 7 | Rehearse and resolve only material issues | Full 20-minute delivery, checked files, working local demonstration, backup answers |

## Work to protect

The required finish is a clear analysis, working prediction path and small demo,
reproducible setup, and a rehearsed presentation. Finish these before pursuing
additional datasets, extensive tuning, extra endpoints, or visual polish that
does not improve understanding.

A full multivariable logistic comparison is part of the core analysis. A faithful
reconstruction of the published classifier and an external-cohort study are useful
extensions, but they should not consume the week. Keep cloud work small. If access
is unavailable, state that and use the tested local container for the interview.

## Current and planned work

As of September 15, 2026, the initial analysis, model comparison, error review,
uncertainty and score-reliability assessment, and shared preprocessing/prediction
package are complete. The fixed procedure (27 fits across three binary targets)
was rerun through that package;
all nine evaluation prediction tables matched the preserved baseline exactly.
The README links to reports, editable charts, and verification records.

The bounded [rejection subtype follow-up](../results/followup/20260915_subtypes/REPORT.md)
is complete. Five new candidates were fitted using the same saved split.
Four-class logistic regression recognized 10 of 18 mixed diagnoses with 5 false
mixed calls, compared with 10 and 13 for the separate component models. The
four-class models did not improve the frozen binary model's rejection error
counts. The service continues to use the binary model.

The [FastAPI service and HTML demonstration](API.md) are complete. They support
prepared public examples and validated CSV uploads, return a versioned score and
flag, and explain invalid input. All 64 tests pass after the audit. A real HTTP check reproduced
all 345 validation scores within `1e-12` of CLI and saved results. The
[verification guide](VERIFICATION.md) records the clean-install checks and CI
workflow. The repository's GitHub remote is configured; pushes and pull requests
trigger the hosted checks.

The [defensibility and implementation audit](AUDIT.md) is complete on
`audit/defensibility-and-elegance`. It fixes ambiguous input handling, consolidates
analysis checks, derives report claims from measured results, and simplifies the
README. The methods, fitted model, and frozen threshold are preserved. The audit
documents the narrow model-selection margin and the limits of assay quality checks.
A second pass makes the training and prediction workflows explicit, expands dense
calculations, and gives each chart its own function. Its full 27-fit reproduction
retains all nine evaluation tables exactly; the service keeps its frozen model.

Remaining project work is the interview presentation and deployment preparation,
including a local container run and a small cloud demonstration if access permits.
