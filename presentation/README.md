# Interview presentation

Revised September 21, 2026. **Classifying Kidney Transplant Rejection from Biopsy
RNA** has **19 main slides and no backup slides**, planned for a full
**20-minute talk** with questions afterward. The current revision centers the
classifier choice within an established molecular application in rejection assessment. It explains
the screening selection, validation advantage and existing split-stability result.
Cross-validation remains a proposed next step. The sequence and planned timings
are unchanged. The report and application are the only live demonstrations.

- [Editable PowerPoint](unos_kidney_biopsy.pptx)
- [Separate HTML speaking script](speaking_script.html)
- [Matching PDF](unos_kidney_biopsy.pdf)
- [Offline analysis report](analysis_report.html)
- [Captured demonstration fallback](demo_fallback.html)

Open the HTML script in a browser. It contains the spoken text, matching slide
previews, brief delivery cues, source links, and approximate pacing estimates.
Click a slide preview to enlarge it. Expand “On this slide” to review its topic
cues. The text and images work offline. The sidebar, previous/next controls,
reading-size controls, and rehearsal timer help with practice. Printing includes
the full script. Repository source links require keeping the file in this folder.

**The PowerPoint contains no speaker notes or notes pages.** All spoken material
belongs in the HTML file. The presentation before this reframing is preserved
privately under `build/presentation/before-reframing-20260921/presentation/`.
The version before restoring Banff is preserved under
`build/presentation/before-banff-purpose-20260921/presentation/`.

## Story and timing

| Slides | Subject | Planned allocation |
| --- | --- | ---: |
| 1–12 | Accepted context, methods, and validation results | 11:25 |
| 13 | Inspecting the analysis report, live | 0:45 |
| 14 | One public specimen through the service, live | 2:00 |
| 15 | Shared preparation and scoring | 1:10 |
| 16 | An interface other software can call | 1:10 |
| 17 | Checking the application against the analysis | 1:35 |
| 18 | Running and maintaining the application | 1:10 |
| 19 | What this project accomplished | 0:45 |
| | **Total** | **20:00** |

These are approximate allocations, not measured rehearsal results. Use the
HTML's per-slide times as pacing aids. Complete two full aloud rehearsals and one
fallback rehearsal before the interview. The HTML page can export a measured
rehearsal record. Review the account of personal contributions before presenting.

The opening connects an established molecular application to a modeling decision:
what does a more complex classifier contribute before further validation? It
explains the biopsy, the project purpose, Banff and Zhang's model comparison
before the dataset and methods. Slide 12 shows the validation
errors. The next report stop demonstrates how another analyst can inspect the
saved analysis. It does not repeat the results presentation. After the application
demo, the implementation slides explain shared preparation, the API, agreement
with saved research results, and how another developer could run and check the
software. Short code excerpts appear on the slides. The complete
[Code Guide](../docs/CODE_GUIDE.html) remains available for questions.

The [presentation specification](../docs/PRESENTATION_SPEC.md) records the
sequence and time budget. The [guide](../docs/PRESENTATION_GUIDE.md) records the
user's presentation preferences and the dated design and rehearsal sources.
The former detailed-results and backup slides are removed from the current deck.
Their saved analyses and source documentation remain available.

## What changed in this revision

| Slide | Change |
| --- | --- |
| 1 | Narration connects the established application to the classifier choice; the visual title is unchanged. |
| 2 | Spoken transition introduces the recognized molecular application. |
| 3 | States the purpose: assess what a more complex classifier contributes before further validation, and preserve the evaluated procedure in software. |
| 4 | Restores Banff's role for validated transcript tests. Explains Zhang's model comparison and choice of LASSO. Retains why both errors matter. |
| 10 | Narration makes logistic versus CatBoost the main comparison, supported by IFNG and the constant benchmark. |
| 11 | Shows both models detecting 157/174 screening rejection cases, with five versus six false positives among 89 no-rejection specimens. |
| 12 | Retains the validation chart and explains the eight fewer misses with equal false positives, the paired uncertainty and the 13-to-seven discovery split result. |
| 19 | Returns to evidence for the classifier choice and software that preserves it, then proposes cross-validation and direct evaluation of this score's added diagnostic value. |

Across the September 21 revisions, visible slides 3, 4, 11, 12 and 19 change.
Narration also changes on slides 1, 2 and 10. This final purpose revision changes
visible slides 3, 4 and 19 and narration on 1, 2, 3, 4 and 19; it preserves the
earlier model-choice explanation. See the
[purpose note](../docs/references/PRESENTATION_PURPOSE_20260921.md) and the
[earlier reframing record](../docs/references/PRESENTATION_REFRAMING_20260921.md).
The 787/263 development split, fitted models, thresholds and saved results remain
the completed analysis. No k-fold experiment was run for this revision.

## Report and application demonstrations

Open [the offline report](analysis_report.html) before the talk. It renders the
preserved [primary analysis report](../results/analysis/20260915_baseline/REPORT.md)
so the audience can see the detailed model comparison and supporting checks.
Briefly show its contents and one useful section. Keep the report's provenance
and linked source visible when explaining how another analyst can inspect the
work. The report is historical evidence and this presentation revision does not
change its results.

Follow [the application guide](../docs/API.md) to start the local service:

```powershell
uv run --frozen uvicorn kidney_biopsy.api:app --host 127.0.0.1 --port 8765 --no-access-log
```

Use the prepared **No Rejection** example, GSM6510425, then **Try an incomplete
file**. The frozen model is `20260915_shared:any_rejection:catboost_all_depth4`.
Its threshold is `0.8765880870219778`. The valid example scores
`0.27493421380277305`. Removing IFNG returns the missing-target error with no score.
These examples come from discovery screening and are not additional validation.
The model and threshold are unchanged.

The fallback HTML embeds actual browser captures from September 18. It requires
no server. If the live app fails, identify the page as a captured run and continue
the same explanation. Return to slide 15 after the report and application stops.
Rehearse both browser transitions as part of the 20-minute talk.

## Evidence and edits

The slides use preserved project results. The validation-error comparison is a
native editable PowerPoint chart with embedded data. The new code excerpts,
tables, and process diagrams remain editable. The PDF is a static rendering of
the final slide pages.

- Numeric sources: [primary analysis](../results/analysis/20260915_baseline/REPORT.md),
  [stability follow-up](../results/followup/20260917_stability/REPORT.md), and
  [subtype follow-up](../results/followup/20260915_subtypes/REPORT.md). Detailed
  follow-up analyses remain available for questions.
- Software evidence: [September 17 local checks](../results/checks/20260917_coherence/README.md).
  The recorded HTTP/CLI comparison covered all 345 validation specimens,
  including reordered input columns. Scores agreed within numerical tolerance
  and flags matched. This checks software consistency.
- Handoff: [verification guide](../docs/VERIFICATION.md),
  [API guide](../docs/API.md), and [container instructions](../docs/CONTAINERS.md).
  Local container checks and a prior hosted CI pass are dated evidence. The
  [AWS guide](../docs/AWS_DEPLOYMENT.md) documents a procedure. Cloud deployment
  has not been performed.
- Study population: the [full-study review](../docs/references/STUDY_AUDIT_20260919.md)
  records 1,193 transplant biopsies and 202 native-kidney controls among the
  1,395 specimens, processing at one laboratory, undocumented patient and
  referring-center separation, and excluded diagnosis categories. The existing
  results still use every deposited specimen.
- Clinical context: Banff includes validated biopsy transcript tests in defined
  settings for antibody-mediated rejection. Zhang et al. (2024) compared model
  families for four recorded diagnoses and selected LASSO for similar accuracy
  with fewer features. This project examines a binary classifier choice within
  that established application. Added diagnostic value from this particular
  score needs direct evaluation. See
  [Research context](../docs/RESEARCH_CONTEXT.md).
- Basic biology: NIDDK's kidney transplant and biopsy pages. The script contains
  full links beside the relevant passages. The
  [biopsy-care review](../docs/references/BIOPSY_CARE_20260919.md) and
  [wording source note](../docs/references/PRESENTATION_WORDING_20260921.md)
  support the explanation of potential harm from missed rejection and unnecessary
  rejection treatment, and the study of borderline diagnoses.
- [Presentation guide](../docs/PRESENTATION_GUIDE.md) supplies dated design and
  rehearsal references. [Source and output hashes](manifest.json) identify the
  current draft.

This wording pass changes the presentation and its documentation. It does not change
the research runs, scoring software, or frozen model. No new software test run,
cloud deployment, aloud rehearsal, or PowerPoint-desktop presentation test is
claimed by this documentation.

## Source files

- `source/build_deck.mjs`: slide content and native charts/tables.
- `source/technical_slides.mjs`: replacement slides 13–19, with excerpts read
  from the project source code.
- `source/build_analysis_report.mjs`: offline view of the preserved primary
  analysis report, using the bundled Node runtime and `marked`.
- `source/speaking_script.json`: spoken paragraphs, delivery cues, and timings.
- `source/build_script_html.py`: offline HTML script reader.
- `source/remove_notes.py`: removes the exporter's blank notes package parts.
- `source/render_final.mjs`: renders the final PowerPoint for the PDF and HTML.
- `source/build_backups.py`: PDF and captured-demo HTML.
- `assets/`: actual application captures. `slides/`: final slide previews.

Run commands from the repository root. Deck authoring uses the Codex bundled
Node runtime and `@oai/artifact-tool`. The PDF builder uses bundled Python with
ReportLab. Set `PRESENTATION_SKILL_DIR`, `RUNTIME_PYTHON`, and
`RUNTIME_NODE_MODULES` to the installed bundled runtime paths. Provide the runtime
packages through `build/presentation/node_modules`. Use a new `DECK_FILENAME`
when preserving a later revision. The finalizer refuses to overwrite a deck.

The canonical filename is used by `render_final.mjs`, the PDF builder, and the
HTML links. After the finalizer validates a new revision, copy that PPTX to
`presentation/unos_kidney_biopsy.pptx`, preserving the prior draft in the private
build directory. Render the canonical deck, rebuild the PDF, and rebuild the HTML.
The rendering and package checks derive the slide count from the deck and script.
Build the offline report with the same bundled Node runtime:

```powershell
node presentation/source/build_analysis_report.mjs
```

After a script-only edit:

```powershell
uv run --frozen python presentation/source/build_script_html.py --require-images
```

Update the source/output hashes after revising deliverables. Temporary builds and
validation reports stay under the Git-ignored `build/presentation/` directory.
