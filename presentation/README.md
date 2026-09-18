# Interview presentation

First complete draft, September 18, 2026. The talk has **14 main slides** with a
**20:00 speaking plan**, followed by **6 backup slides** for questions.

- [Editable PowerPoint](unos_kidney_biopsy.pptx)
- [Separate HTML speaking script](speaking_script.html)
- [Matching PDF backup](unos_kidney_biopsy.pdf)
- [Captured demonstration backup](demo_fallback.html)

Open the HTML script in a browser. It contains the spoken text, matching slide
previews, separate delivery cues, source links, and planned cumulative timings.
The text and images work offline. The sidebar, previous/next controls, reading-size
controls, and rehearsal timer help with practice. Printing includes the full script.
Repository source links require keeping the file in this folder.

**The PowerPoint contains no speaker notes or notes pages.** All spoken material
belongs in the HTML file, following the user's September 18 instruction.

## Story and timing

| Slides | Subject | End time |
| --- | --- | ---: |
| 1 | Question and early result | 0:45 |
| 2–3 | Biopsy, rejection, RNA and the assay | 4:15 |
| 4–6 | Observations, preparation and fair comparison | 9:00 |
| 7–9 | Errors, diagnosis groups and comparison uncertainty | 14:00 |
| 10–12 | Shared software, demonstration and checks | 18:15 |
| 13–14 | Limits, next evidence and conclusion | 20:00 |
| 15–20 | Backup material | Questions afterward |

The 2,244-word main script includes a two-minute demonstration and time for
pauses. These are planned allocations, not measured rehearsal results. Complete
two full aloud rehearsals and one fallback rehearsal before the interview. The
HTML page can export a measured rehearsal record. The candidate should also
review the account of personal contributions before presenting.

## Demonstration

Follow [the application guide](../docs/API.md) to start the local service:

```powershell
uv run --frozen uvicorn kidney_biopsy.api:app --host 127.0.0.1 --port 8765 --no-access-log
```

Use the prepared **No Rejection** example, GSM6510425, then **Try an incomplete
file**. The frozen model is `20260915_shared:any_rejection:catboost_all_depth4`.
Its threshold is `0.8765880870219778`. The valid example scores
`0.27493421380277305`. Removing IFNG returns the missing-target error with no score.
These examples come from discovery screening and are not additional validation.

The fallback HTML embeds actual browser captures from September 18. It requires
no server. If the live app fails, identify the page as a captured run and continue
the same explanation.

## Evidence and edits

The slides use the project's preserved results. The main error comparison and
reliability chart are native editable PowerPoint charts with embedded data.
Tables and process diagrams are also editable. Reliability chart coordinates
are rounded to six decimals for workbook portability; the source CSV retains
full precision. The PDF is a static rendering of the final slide pages.

- Numeric sources: [primary analysis](../results/analysis/20260915_baseline/REPORT.md),
  [stability follow-up](../results/followup/20260917_stability/REPORT.md),
  [subtype follow-up](../results/followup/20260915_subtypes/REPORT.md).
- Software evidence: [September 17 local checks](../results/checks/20260917_coherence/README.md).
- Basic biology: NIDDK's kidney transplant and biopsy pages. Assay context: the
  original study and Bruker's nCounter documentation. Exact links accompany the
  relevant passages in the speaking script.
- [Presentation guide](../docs/PRESENTATION_GUIDE.md) supplies the dated design
  and rehearsal references.
- [Source and output hashes](manifest.json) identify this draft.

The deck was rendered and visually reviewed, its package and native evidence
checked, and the HTML navigation and reading controls exercised in a browser.
The live valid/invalid demonstration was replayed. No aloud rehearsal or
PowerPoint-desktop presentation test is claimed.

## Source files

- `source/build_deck.mjs`: slide content and native charts/tables.
- `source/speaking_script.json`: spoken paragraphs, delivery cues and timings.
- `source/build_script_html.py`: offline HTML reader.
- `source/remove_notes.py`: removes the exporter's blank notes package parts.
- `source/render_final.mjs`: renders the final PowerPoint for the PDF and HTML.
- `source/build_backups.py`: PDF and captured-demo HTML.
- `assets/`: actual application captures. `slides/`: final slide previews.

Run commands from the repository root. Deck authoring uses the Codex bundled
Node runtime and `@oai/artifact-tool`; the PDF builder uses bundled Python with
ReportLab. Set `PRESENTATION_SKILL_DIR`, `RUNTIME_PYTHON`, and
`RUNTIME_NODE_MODULES` to the installed bundled runtime paths. Provide the runtime
packages through `build/presentation/node_modules`. Use a new `DECK_FILENAME`
when preserving a later revision. The finalizer refuses to overwrite a deck.

The current final filename is used by `render_final.mjs`, the PDF builder, and
the HTML links. Update those together when publishing a differently named revision.
After a slide edit, render the final deck, rebuild the PDF, and rebuild the HTML.
After a script-only edit:

```powershell
uv run --frozen python presentation/source/build_script_html.py --require-images
```

Update the source/output hashes after revising deliverables. Temporary builds and
validation reports stay under the Git-ignored `build/presentation/` directory.
