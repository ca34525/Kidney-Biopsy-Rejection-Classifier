# Interview presentation

Revised September 20, 2026. **Classifying Kidney Transplant Rejection from Biopsy
RNA** has **20 main slides** planned for a full **20-minute talk**, followed by
**8 backup slides** for questions.

- [Editable PowerPoint](unos_kidney_biopsy.pptx)
- [Separate HTML speaking script](speaking_script.html)
- [Matching PDF backup](unos_kidney_biopsy.pdf)
- [Captured demonstration backup](demo_fallback.html)

Open the HTML script in a browser. It contains the spoken text, matching slide
previews, brief delivery cues, source links, and approximate pacing estimates.
Click a slide preview to enlarge it. Expand “On this slide” to review its topic cues.
The text and images work offline. The sidebar, previous/next controls, reading-size
controls, and rehearsal timer help with practice. Printing includes the full script.
Repository source links require keeping the file in this folder.

**The PowerPoint contains no speaker notes or notes pages.** All spoken material
belongs in the HTML file, following the user's September 18 instruction.

## Story and timing

| Slides | Subject | Approximate time |
| --- | --- | ---: |
| 1–4 | Title, transplant context, possible use, and supporting evidence | 3½ minutes |
| 5–8 | Dataset, outcome, measurements, and normalization | 3½ minutes |
| 9–11 | Study groups, models, and threshold | 2¾ minutes |
| 12–15 | Validation errors, uncertainty, and model-choice results | 4¾ minutes |
| 16–18 | Shared software, demonstration, and checks | 3¾ minutes |
| 19–20 | Possible extensions and project accomplishments | 1¾ minutes |
| 21–28 | Backup material, starting with assay details | Questions afterward |

The main script includes about two minutes for the demonstration and room for
pauses. These are approximate allocations, not measured rehearsal results.
Use the HTML's per-slide times as pacing aids. Actual rehearsals determine the
pace; individual slide estimates need not be optimized to exact seconds. Complete
two full aloud rehearsals and one fallback rehearsal before the interview. The
HTML page can export a measured rehearsal record. The candidate should also
review the account of personal contributions before presenting.

The opening slide contains only the selected title. The speaker introduces the
research question aloud. Immediately after the biopsy explanation, the
talk explains why a molecular second opinion could help specialists assess
uncertain biopsies. Banff guidance and B-HOT research support this motivation.
The project's measured contribution is a reproducible classifier and working
software. Testing added benefit in uncertain cases is a possible extension
requiring clinical collaborators. Slide 4 explains why an incorrect rejection
diagnosis could lead to harmful unnecessary treatment, without claiming that this
project improves care. The [biopsy-care review](../docs/references/BIOPSY_CARE_20260919.md)
records the supporting research.
The main sequence then introduces the dataset, the outcome, and the measurements
before explaining evaluation. Slide 2 uses bold definitions with evidence
sub-bullets. Slide 3 uses two matching hypothetical-example boxes. Slide 5 shows
two linked analysis tables, with their assembly explained in the script. The
patient and referring-center separation note sits beneath the dataset counts.
"Cohort" first appears with the study groups on slide 9. Detailed assay terminology
is on backup slide 21. Recall and precision introduce the error terms before the
validation chart compares false negatives and false positives. Slide 11 uses
word fractions for those metrics and remains unchanged. The model tables and
validation chart distinguish IFNG only (Logistic regression) from All RNA
(Logistic Regression). Slide 14 explains how the paired bootstrap produced the
recall-difference interval and why a separate check of the development split was
needed. Slide 15 shows how the 20 discovery-only splits were made and presents the
model-selection counts in a table. Slide 16 introduces the service
and demo, slide 19 presents hypothetical extensions, and slide 20 separates the completed
model comparison from the software demonstration. Substantive topics
have visible support, with spoken elaboration in the script.
The [presentation specification](../docs/PRESENTATION_SPEC.md)
records the outline and approximate section budget, and the [guide](../docs/PRESENTATION_GUIDE.md)
records the September 19 and 20 feedback and standards for future edits.

The supplied full article and supplements clarify the study population. The
1,395 specimens include 1,193 transplant biopsies and 202 native-kidney controls.
All specimens were processed at one laboratory. Patient and referring-center
separation are not documented. Some difficult diagnostic categories, including
borderline acute T-cell-mediated rejection, were excluded. The slides and script
reflect those findings. Exact pages and supporting details are in the
[full-study review](../docs/references/STUDY_AUDIT_20260919.md).

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

The slides use the project's preserved results. Two native editable PowerPoint
charts contain embedded data: the main validation error comparison and the backup
reliability chart. Slide 14 explains the 2,000 paired bootstrap resamples with
fixed models and thresholds. Slide 15 uses an editable split diagram and a table
of screening selections: CatBoost 13/20 and All RNA (Logistic Regression) 7/20.
The assessment-error dot plots are omitted from the deck; the saved analysis
outputs remain available. Tables and process diagrams are editable. Reliability chart coordinates
are rounded to six decimals for workbook portability; the source CSV retains
full precision. The PDF is a static rendering of the final slide pages.

- Numeric sources: [primary analysis](../results/analysis/20260915_baseline/REPORT.md),
  [stability follow-up](../results/followup/20260917_stability/REPORT.md),
  [subtype follow-up](../results/followup/20260915_subtypes/REPORT.md).
- Software evidence: [September 17 local checks](../results/checks/20260917_coherence/README.md).
- Basic biology: NIDDK's kidney transplant and biopsy pages. Assay context: the
  original study and Bruker's nCounter documentation. Exact links accompany the
  relevant passages in the speaking script.
- Full-study evidence: the [September 19 review](../docs/references/STUDY_AUDIT_20260919.md)
  of the supplied article and supplements supports the population, cohort,
  IFNG-benchmark, and error-tradeoff explanations. The reported evaluation still
  uses every deposited specimen and the preserved model and threshold.
- Clinical rationale: current Banff guidance and Rosales et al. (2022), documented
  in [Research context](../docs/RESEARCH_CONTEXT.md). The later-outcome association
  in that B-HOT study motivates further research and is not a forecast produced
  by this classifier. A backup slide cites UNOS's June 2026 kidney-photo study
  as an example of research toward supporting expert assessment in another task.
- [Presentation guide](../docs/PRESENTATION_GUIDE.md) supplies the dated design
  and rehearsal references.
- [Source and output hashes](manifest.json) identify this draft.

The demonstration captures come from the first draft's valid and invalid local
requests. The revised slide sequence does not change the service or its model.
No aloud rehearsal or PowerPoint-desktop presentation test is claimed.

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

The canonical filename is used by `render_final.mjs`, the PDF builder, and the
HTML links. After the finalizer validates a new revision, copy that PPTX to
`presentation/unos_kidney_biopsy.pptx`, preserving the prior draft in the private
build directory. Render the canonical deck, rebuild the PDF, and rebuild the HTML.
The rendering and package checks derive the slide count from the deck and script.
After a script-only edit:

```powershell
uv run --frozen python presentation/source/build_script_html.py --require-images
```

Update the source/output hashes after revising deliverables. Temporary builds and
validation reports stay under the Git-ignored `build/presentation/` directory.
