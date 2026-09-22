# Continuous engineering demonstration

September 22, 2026. Implements the user's request to remove most technical slide
pages, build the proposed HTML engineering deliverable, use the established slide
palette for the slide 12 follow-up count, and incorporate KDIGO into slide 4.

## Implemented sequence

The current deck has 14 pages. Slides 1–12 retain their order; slide 13 introduces
the software demonstration, and slide 14 closes on the model comparison and
software engineering. The browser portion occupies one HTML page with three stops:

| Stop | Selected content | Planned time |
| --- | --- | ---: |
| Evidence | Errors by recorded diagnosis, the saved discovery follow-up, expandable 20-selection record and complete reports | 1:15 |
| Application | The real FastAPI application's complete public example, preparation, score/threshold/flag, and missing-IFNG response | 2:15 |
| Engineering | Shared training/prediction excerpts, real API request/response, 345-specimen agreement check, consequential failures and handoff evidence | 4:00 |

Together with 11:25 for slides 1–12, a 0:15 transition and a 0:50 closing, the
planned talk remains 20 minutes. The separate script includes browser-stop
narration and actions between slides 13 and 14. No PowerPoint notes are used.

## Why these stops fit the role and audience

The supplied [UNOS position description](JOB_DESCRIPTION.txt) emphasizes converting
analytical prototypes into maintained software, transforming data, supporting
training/testing/deployment, APIs and rapid prototyping. It also asks for clear
communication. The demonstration selects evidence for those responsibilities:

- The saved reports let the biostatisticians inspect subgroup errors and the
  dependence of model choice on discovery splitting. They give the public-health
  audience concrete consequences without another full metrics lecture.
- A complete specimen and a missing-target failure show a usable prototype,
  interpretable output and input handling. This connects the analysis to something
  an analyst or laboratory researcher can actually try.
- Shared normalization and prediction source show how data preparation reaches
  the service without a duplicate implementation. The request/response makes the
  interface explicit for the data scientist. The agreement check and handoff
  records show how another developer can check and run the calculation.

These are reasons for selecting the content, not claims about an unpublished
interview rubric. The project does not demonstrate cloud deployment, production
clinical use or terabyte-scale processing.

## Implementation and evidence

`presentation/engineering_demo.html` embeds its styles, behavior, selected data,
17 source documents/records, and actual saved example responses. The reference
library includes complete primary and follow-up reports, the API and verification
guides, the Code Guide and code/CSV/JSON evidence. Source hashes are recorded in
`presentation/engineering_demo_sources.json`.

`presentation/source/serve_demo.py` adds presentation-file serving alongside the
unchanged research FastAPI application. It binds to localhost. The HTML verifies
the expected model version and threshold before loading the live application in
an iframe. The surrounding page supplies the title, so the embedded view hides
the app's duplicate header and introduction while retaining its controls and
results. Requests still use the actual service and shared prediction code.

The response snapshot was captured from the existing application with the saved
model through FastAPI's TestClient. The complete public specimen returns score
`0.27493421380277305`, threshold `0.8765880870219778` and a false rejection flag.
Missing IFNG returns HTTP 422 and no predictions. Saved responses are explicitly
labeled and remain usable when the file is opened without a server. The original
captured-browser fallback remains available as well.

The highlighted 345-specimen check remains the dated September 17 record. New
presentation checks do not change its date or imply rerunning the model comparison.
The model, thresholds, research outputs and application source are preserved.

## Slide details

Slide 12 now uses teal `#007C78` for the discovery-split statement, matching
existing emphasis. The chart retains orange missed cases and teal incorrect flags.

Slide 4 retains Banff and Zhang and expands its existing error-consequence section:
biopsy findings help guide rejection treatment. The script cites
[KDIGO 2009, recommendation 6.1](https://kdigo.org/wp-content/uploads/2017/02/KITxpGL_summary.pdf),
including the exception when biopsy would substantially delay treatment. KDIGO
supports the treatment connection; it does not validate this classifier. The
[biopsy-care review](BIOPSY_CARE_20260919.md) supplies the infection context.

The previous deck and documents are preserved in
`build/presentation/before-engineering-demo-20260922/`. Source and output checks
are recorded with the new package. Timed rehearsals remain separate work.
