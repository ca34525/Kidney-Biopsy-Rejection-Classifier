# Software verification

Run these commands from the project root using Python 3.12 and uv. Every saved
check record uses a new destination so earlier results remain available.

## Fast checks

```powershell
uv sync --frozen
uv run --no-sync ruff check src scripts tests experiments
uv run --no-sync ruff format --check src scripts tests experiments
$checkName = Get-Date -Format 'yyyyMMdd-HHmmss'
uv run --no-sync python scripts/check_project.py --output "results/checks/$checkName/checks.json"
```

Ruff checks for basic Python mistakes, unused or undefined names, and import order.
Its formatter gives the source a consistent layout, with a target line length of
100 characters. The pinned development version and small rule list are in
`pyproject.toml`. The two commands above report problems without changing files.
To apply import fixes and formatting while editing, run:

```powershell
uv run --no-sync ruff check --fix src scripts tests experiments
uv run --no-sync ruff format src scripts tests experiments
```

Review the diff after applying fixes. The configuration excludes `results`,
`data`, build output, and caches, including when a preserved file is named
explicitly. Completed runs keep their original source snapshots. Three research
scripts allow imports after their local-path or plotting setup; this is the only
file-specific lint exception. Ruff is not a static type checker. Its
[configuration](https://docs.astral.sh/ruff/configuration/) and
[rule reference](https://docs.astral.sh/ruff/rules/) explain the selected checks.

The final command checks Python syntax, parses the project and lock TOML files,
checks the local package and its HTML/CSS/JavaScript assets, and runs the test suite.
Tests use small generated fixtures and require no public downloads or trained
research model. The JSON records source hashes, package versions, test counts,
failures, and elapsed time. Lint and formatting results appear separately in the
terminal and CI log so a failed check is easy to identify.

The [CI workflow](../.github/workflows/checks.yml) runs the same checks after
`uv sync --locked --no-editable` on Python 3.12. `--locked` fails if dependency
declarations disagree with the lockfile. The noneditable installation builds
and installs the package, so missing packaged web assets fail the check. Lint and
format checks run before tests. CI saves the small JSON evidence as an artifact.
The workflow then builds a container with a tiny synthetic CatBoost model and
checks readiness, predictions, displayed error counts, and invalid input over
HTTP. Both JSON check records are retained. Full research model training stays
outside CI. See the [container guide](CONTAINERS.md) for the same commands locally.

The workflow uses the documented interfaces for [checkout](https://github.com/actions/checkout),
[setup-uv](https://github.com/astral-sh/setup-uv), and
[upload-artifact](https://github.com/actions/upload-artifact), checked on
September 15, 2026. The workflow is configured locally; an actual hosted CI pass
requires a repository push and a completed GitHub Actions run.

## CI and container checks: September 17, 2026

The [verification record](../results/checks/20260917_ci_docker/README.md) contains
78 passing tests and successful runs of both the real research image and the
synthetic CatBoost image used in CI. Four public examples matched local research
scores exactly, and the invalid example was rejected. Both images served the
expected page, examples, and evaluation counts with an unprivileged user and a
read-only filesystem. See [container setup](CONTAINERS.md) and the prepared
[AWS deployment steps](AWS_DEPLOYMENT.md). No AWS deployment has been performed.

## Fresh environment and application check

This check uses the current project files and the frozen model from the selected
local run. It makes physical copies in a new ignored directory, creates a new
environment and package cache, and installs dependencies from the lockfile.

```powershell
$checkName = Get-Date -Format 'yyyyMMdd-HHmmss'
uv run --no-sync python scripts/verify_fresh_setup.py --run-dir results/reproduction/20260915_shared --check-dir "data/processed/setup_checks/$checkName" --output "results/checks/$checkName/fresh_setup.json"
```

The command verifies:

1. Source, raw data, and the selected model were physically copied with matching
   hashes. Source folders are explicitly selected; environments, caches, other
   analyses, and nested setup-check directories are excluded.
2. The copy installs its own package and dependencies with
   `uv sync --frozen --no-editable`. It imports the installed package from that
   environment, including the web assets.
3. The documented downloader accepts and verifies the existing local public
   inputs. The separate source-manifest verification also passes.
4. The fast software checks and tests pass inside the copy.
5. The installed API serves its page, assets, health, and model information. Its
   predictions for two real public specimens match the installed CLI within
   `1e-12`, and a missing-target batch returns a structured error with no scores.

The fresh environment downloads dependency packages, so network access is needed.
Public assay files and this project's selected model are copied for this setup
check; models are not retrained. Raw specimen inputs and CLI outputs stay under
the ignored copy. The aggregate JSON records each copied file's hash, commands,
exit statuses, test evidence, model version, and score agreement. Completed copies
are preserved. This check does not establish container or cloud deployment.

### Completed check: September 15, 2026

The [final fresh-setup record](../results/checks/20260915_application/fresh_setup_final.json)
documents 64 physically copied files, a new environment and installed package,
and **55 passing tests**. Setup and checks took 68.7 seconds. All five checked
page/API routes returned successfully. CLI and API scores differed by at most
`1.11e-16` for the two source specimens, within the `1e-12` tolerance. The
missing-target batch returned HTTP 422 with a structured error. The earlier
passing copy is preserved in the same check directory's first setup record.

## Real HTTP and browser checks

The [HTTP verification record](../results/checks/20260915_application/http/http.json)
compares all 345 saved validation specimens through a real local Uvicorn server,
the command-line predictor, and the preserved evaluation table. Targets are sent
in reverse column order. The largest score difference was `1.11e-16`, within the
`1e-12` tolerance; all flags agreed. Invalid input and a 17-specimen request were
rejected as complete batches.

```powershell
$checkName = Get-Date -Format 'yyyyMMdd-HHmmss'
uv run --frozen python scripts/verify_http_service.py --output-dir "results/checks/$checkName/http" --case-dir "data/processed/application_checks/$checkName"
```

The script starts and stops its own server on an available local port. The
[browser record](../results/checks/20260915_application/browser.json) documents
visible valid/invalid results, a two-specimen file upload, clearing stale scores
when changing input, and rejecting a response from a changed server model until
the page is reloaded. JavaScript syntax was checked with
`node --check src/kidney_biopsy/static/app.js`. The demo requires no Node runtime;
Node was used only for this syntax check.

## Existing analysis evidence

### Defensibility and implementation audit: September 15, 2026

The [audit report](AUDIT.md) explains the fixes and the retained methodological
limits. The [final check record](../results/checks/20260915_audit/final.json)
contains **64 passing tests**. The new
[HTTP check](../results/checks/20260915_audit/http/http.json) reproduces all 345
validation scores within `1.11e-16` with identical flags. The
[report comparison](../results/checks/20260915_audit/report_comparison.json) confirms
byte-for-byte agreement for all 14 aggregate CSVs and the primary metrics JSON.
New analysis manifests include the source hashes of the shared helpers they use.
The [preserved-run check](../results/checks/20260915_audit/preserved_runs.json)
verifies existing model and run artifacts. No model fitting or dependency changes
were part of that initial pass.

### Readability refactor: September 15, 2026

The second pass reorganized the main workflows and expanded dense calculations.
All [64 existing tests](../results/checks/20260915_readability/checks.json) pass.
A [full 27-fit reproduction](../results/checks/20260915_readability/reproduction.json)
matches all nine original evaluation tables exactly, including split assignments,
model choices, and thresholds. The new run has its own source snapshots.

The [HTTP check](../results/checks/20260915_readability/http/http.json) confirms
CLI/API/saved-score agreement on all 345 validation specimens. The
[browser check](../results/checks/20260915_readability/browser.json) covers valid,
invalid, batch, stale-result, and changed-model behavior. The
[analysis comparison](../results/checks/20260915_readability/analysis_comparison.json)
confirms byte-for-byte agreement for eight aggregate tables, the metrics JSON,
and all six PNG charts on the real data. No dependencies were changed.

### Earlier analysis checks

The [shared-code reproduction](../results/checks/20260915_shared/reproduction.json)
compares the fixed training procedure with the preserved baseline. The associated
[test record](../results/checks/20260915_shared/tests.json) and
[model reload check](../results/checks/20260915_shared/reproduced_inference.json)
document the earlier acceptance checks. New application checks supplement those
records and do not overwrite them.
