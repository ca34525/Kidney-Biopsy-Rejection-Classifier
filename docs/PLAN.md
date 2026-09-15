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

The repository's README records what currently runs and links to locally generated
results. This plan describes the intended sequence, not a claim that the API,
container, CI, cloud deployment, or slides are already finished. Update progress
after actual checks, and keep each next step small enough to complete.
