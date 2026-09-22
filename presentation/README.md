# Interview presentation

Updated September 22, 2026. The presentation has **14 main slides**, one continuous
browser demonstration and a separate speaking script. Its planned **20 minutes**
include the demonstration; questions follow. PowerPoint notes are empty.

- [Editable PowerPoint](unos_kidney_biopsy.pptx)
- [Matching PDF](unos_kidney_biopsy.pdf)
- [Complete HTML speaking script](speaking_script.html)
- [Engineering demonstration](engineering_demo.html)
- [Full primary analysis report](analysis_report.html)
- [Earlier captured application images](demo_fallback.html)

## Presentation flow

| Part | Planned time | Cumulative time |
| --- | ---: | ---: |
| Slides 1–12: purpose, context, methods and results | 11:25 | 11:25 |
| Slide 13: software engineering transition | 0:15 | 11:40 |
| Browser: inspect the saved evidence | 1:15 | 12:55 |
| Browser: score a public specimen | 2:15 | 15:10 |
| Browser: shared calculation, API, checks and handoff | 4:00 | 19:10 |
| Slide 14: completed analysis, software and next steps | 0:50 | 20:00 |

Switch from PowerPoint to the browser after slide 13. The Application stop opens the scoring app in a separate tab. Return to the
engineering page for the third stop, then to PowerPoint on slide 14. The former technical
slides have been removed from the current deck. Their useful content is now in
the browser page and script.

The first stop explains the validation cohort and the repeated discovery-split
design before showing their results. The second shows a real CSV excerpt and
one link to the scoring application. The third shows
source excerpts, a real API response and the saved 345-specimen agreement check,
followed by the run instructions, automated checks and local container evidence.

Full reports and source records open inside the page's **Reports and sources**
dialog. They also have source downloads. The page includes the primary report,
discovery follow-up, API and verification guides, Code Guide, actual source
excerpts and original evidence CSV/JSON. It uses the slide palette: teal
`#007C78`, orange `#B55730`, ink `#16343E` and pale background `#F7F8F5`.

## Start the live demonstration

From this project's root on the Mac, use the existing environment:

```sh
.venv/bin/python presentation/source/serve_demo.py
```

With uv installed (including from PowerShell):

```powershell
uv run --frozen python presentation/source/serve_demo.py
```

Open [the local engineering demonstration](http://127.0.0.1:8766/presentation/engineering_demo.html).
The launcher and saved-response capture both use `source/demo_config.json`, which
explicitly selects `results/reproduction/20260922_mac_clone` and its prepared examples.
Keep the terminal running; Ctrl+C stops the server. Port 8766 serves both the
engineering page and scoring app. The standalone application on port 8765 is a
separate process and does not inherit this presentation configuration.
The Application tab links to the scoring app at the server root. The integration
check verifies the served model version and threshold against the saved example.
The launcher binds to localhost and adds presentation-file serving around the
existing FastAPI application. It does not change the model or scoring routes.
Use `--port` to select a different local port if needed.

If the examples are absent, follow [application preparation](../docs/API.md).
A clean checkout first needs the environment, data and reproduction steps in
the [project README](../README.md). The presentation launcher does not train models.

Before presenting, follow **Kidney biopsy application** from the Application tab.
Choose **No Rejection**, click **Get research score**, and then
**Try an incomplete file**. The complete specimen is GSM6510425, with score
`0.2749342138027727` and frozen threshold `0.8765880870219773`.
Removing IFNG returns HTTP 422 and no score. The model version is
`20260922_mac_clone:any_rejection:catboost_all_depth4`.

## Offline use and speaking script

Open `engineering_demo.html` directly to read its reports, code, CSV preview and
saved API responses without a server. The Application tab contains no duplicate
scoring interface; its application link requires the local service. The separate
`demo_fallback.html` retains the captured application screenshots for offline use.

The separate speaking script contains the words to say, click instructions,
fallback wording and pacing. Its index places browser stops D1–D3 between slides
13 and 14, without creating extra slide pages. It embeds all 14 slide images.
Use its font controls, timer and rehearsal-record export for practice.

Planned timings are not measured rehearsal results. Complete two full timed runs
and one fallback run. If time runs long, shorten source-dialog inspection or
secondary implementation detail before cutting the valid/invalid example.

## Source and build files

- `source/build_deck.mjs`: slides 1–12 and native evidence charts/tables.
- `source/technical_slides.mjs`: transition slide 13 and closing slide 14.
- `source/speaking_script.json`: slide narration plus three browser-stop scripts.
- `source/build_script_html.py`: the offline speaking-script reader.
- `source/build_engineering_demo.mjs`: builds the self-contained demonstration.
- `source/engineering_demo.css` and `.js`: demonstration styles and behavior.
- `source/demo_snapshot.json`: actual captured public-example service responses.
- `source/capture_demo.py`: recreates that snapshot using the existing local model.
- `source/serve_demo.py`: launches the presentation files with the research app.
- `source/check_demo.py`: checks the embedded sources, page structure, script
  order and actual complete/incomplete HTTP responses against the saved example.
- `source/build_analysis_report.mjs`: full primary report rendering.
- `source/render_final.mjs`: renders the final PPTX; `source/build_backups.py`
  creates its matching PDF and the captured-app page.
- `source/record_manifest.py`: checks slide structure and records source/output hashes.

Use the bundled Node runtime and packages for the `.mjs` builders. Deck authoring
uses `@oai/artifact-tool`; the HTML builder uses `marked`. PDF generation uses
bundled Python with ReportLab. Keep the package link at
`build/presentation/node_modules`. The deck builder requires
`PRESENTATION_SKILL_DIR`, `RUNTIME_PYTHON` and `RUNTIME_NODE_MODULES`.
Use a new `DECK_FILENAME` for each finalized revision, then preserve and replace
the canonical PPTX, render it, rebuild the PDF and script, and record the manifest.

After changing demonstration source or embedded reference documents:

```powershell
node presentation/source/build_engineering_demo.mjs
uv run --frozen python presentation/source/build_script_html.py --require-images
```

The snapshot need not be recreated for a text or layout change. If the actual
example or application changes, preserve the previous snapshot before running
`uv run --frozen python presentation/source/capture_demo.py` and rebuilding.
Reload open browser pages after rebuilding; the launcher does not hot-reload HTML.

With the demonstration server running, verify the current package:

```powershell
uv run --frozen python presentation/source/check_demo.py
```

The check records its results under `build/presentation/`. It also compares
retained slide renders when the local pre-revision backup is available.

The previous 19-slide deck and documents are preserved privately under
`build/presentation/before-engineering-demo-20260922/`. The
[revision note](../docs/references/ENGINEERING_DEMO_20260922.md) explains the
selection of browser content and the UNOS role connection. The project's saved
model, threshold and analysis outputs remain unchanged.
