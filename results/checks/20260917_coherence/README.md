# Walkthrough, stability, and consistency checks

Verified September 17, 2026 on `codex/coherent-demo-and-stability`.
These are local checks of the branch. They do not claim a hosted CI pass for
these changes or a cloud deployment.

| Record | Result |
| --- | --- |
| [Installed package](checks.json) | All 94 tests pass; Python 3.12, syntax, packaged static assets, and project-local imports verified. |
| [Real HTTP service](http/http.json) | All 345 author-validation scores and flags agree across saved results, CLI, and HTTP with reordered CSV columns; maximum score difference 1.11e-16 (tolerance 1e-12). Invalid batch and batch-size checks pass. |
| [Rebuilt Docker image](container.json) | Four valid examples, four public walkthroughs, and one invalid example checked. Predictions match exactly; displayed normalization and evaluation match trusted local artifacts. Non-root, read-only runtime and image healthcheck pass. |
| [Browser review](browser_review.json) | Real examples, expanded housekeeping arithmetic, invalid input, selection/upload clearing, and desktop/mobile layouts checked. |
| [Completed stability run](stability.json) | All 204 artifact hashes match; all 20 discovery splits, screening choices, and held-out error counts verified. All 100 saved models reproduce their screening scores exactly. |
| [Preserved reproduction](reproduction.json) | Rechecked the existing nine prediction tables, choices, thresholds, and specimen assignments against the baseline. Maximum score difference 0; this did not retrain models. |
| [Historical artifacts](preserved_runs_after.json) | All 167 artifacts in the baseline, shared, readability, and subtype manifests match their original hashes. |
| [Evidence portability](evidence_portability.json) | 57 analysis/presentation manifest entries match; Git preserves all 86 corrected evidence files with automatic line-ending conversion both enabled and disabled. |

Ruff lint and formatting checks pass across all 35 current Python files.
`node --check src/kidney_biopsy/static/app.js` also passes.
The unit checks include discovery/assessment separation, train-only scaling,
frozen-before-assessment selection, and saved-model reload agreement. The full
20-repeat experiment has its own [results and provenance](../../followup/20260917_stability/REPORT.md).

## Preserving recorded bytes

Before these changes, Git line-ending conversion had changed 11 archived
readability-run source snapshots. Their original manifest was sufficient to
restore the exact recorded bytes, without rewriting the manifest. The
[before record](preserved_runs_before.json) and
[repair record](snapshot_line_endings.json) preserve what was found and restored.

Git had also normalized other archived files in its stored blobs even when
the working files still had the correct original bytes. `results/** -text`
now preserves recorded evidence across Windows and Linux checkouts. The
[Git byte comparison](git_evidence_bytes.json) lists 86 existing evidence files
whose working bytes differ from their earlier Git blobs **only in line endings**.
This includes an original mixed-line-ending source snapshot from the shared run.
The original manifests, model files, predictions, and numerical results retain
their recorded hashes. Use `git diff --ignore-space-at-eol` to inspect substantive
changes without these archival byte corrections.

The [public input manifest](../../../data/manifest.json) also retains its recorded
bytes through an explicit Git attribute; [its portability check](source_manifest_portability.json)
matches the input-manifest hash preserved in the three historical reproduction runs.

## Repeating the software checks

Use fresh output paths; the verification commands preserve existing records.

```powershell
uv sync --frozen --no-editable
uv run --no-sync ruff check src scripts tests experiments
uv run --no-sync ruff format --check src scripts tests experiments
uv run --no-sync python scripts/check_project.py --require-installed --output results/checks/NEW/checks.json
uv run --no-sync python scripts/verify_http_service.py --output-dir results/checks/NEW/http --case-dir data/processed/checks/NEW/http
uv run --no-sync python scripts/prepare_container.py --output-dir build/NEW-container
docker build --build-arg BUNDLE_DIR=build/NEW-container --tag kidney-biopsy:NEW .
uv run --no-sync python scripts/verify_container.py --image kidney-biopsy:NEW --bundle-dir build/NEW-container --output results/checks/NEW/container.json
```
