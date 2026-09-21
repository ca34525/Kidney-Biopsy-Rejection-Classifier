# Source-review corrections, September 21, 2026

This pass reconciles the dated study review with the current documentation,
demo, generated-report wording, and presentation. The
[methodology assessment](../../../docs/METHODOLOGY_REVIEW.md) compares the
implemented procedure with the supplied article and supplements. It does not
add a model experiment.

## Corrections

- Date the article/supplement review explicitly as September 19, 2026.
- State the native-kidney control population beside the demo's validation results
  and in future generated reports, with a link to the dated source audit.
- Put the same context above the fallback's preserved September 18 screenshots
  and retain it in the fallback generator.
- Correct the current README and status to 20 main slides and eight backups.
- Identify the constant baseline's fixed threshold of 0.5 and the all-RNA
  logistic model's C = 0.1 setting in the presentation. IFNG logistic uses C = 1.
- Rebuild the presentation and code guide from their current sources.

## Verification

The existing analysis and API suites passed all 29 tests:

```powershell
uv run --frozen python -m unittest tests.test_analysis tests.test_api
uv run --frozen ruff check scripts/analyze_results.py
git diff --check
```

Ruff and the whitespace check passed. No tests were added merely to repeat the
new wording. A browser inspection of the live local app confirmed that the
334-transplant/11-native-control note is visible beside the eight false flags
and 25 missed cases, with no overlap or clipping. The temporary verification
server was stopped afterward.

The report function was exercised using the baseline's saved aggregate tables
and the normal `load_run()` input loader, without fitting models or recalculating
metrics. The generated scope paragraph contains the source-population counts,
and its relative audit link resolves from the chosen output directory. This was
an ignored local preview, not a replacement for the completed analysis report.

The [preserved-run check](preserved_runs.json) verified all 78 baseline and
shared-run artifacts against their manifests. All nine evaluation prediction
tables, selected models, thresholds, and specimen assignments still agree;
maximum score difference is zero. This compares saved runs, rather than
claiming a new training reproduction.

Presentation package and code-guide checks are recorded in their current
[presentation manifest](../../../presentation/manifest.json) and
[guide manifest](../../../docs/code_guide/build_manifest.json). The corrected
presentation retains 20 main slides, eight backups, two editable charts, and
empty PowerPoint notes. The HTML speaking script retains 20 minutes of planned
timing; no new rehearsal is claimed.
