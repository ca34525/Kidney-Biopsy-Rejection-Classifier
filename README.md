# Kidney biopsy rejection classifier

A self-contained research project for a UNOS Associate Data Scientist interview.
It classifies recorded rejection in an existing kidney transplant biopsy from
public NanoString B-HOT assay measurements.

## Project documents

- [Project specification](docs/PROJECT_SPEC.md): scope, data, evaluation, software, and completion standards.
- [Job requirements](docs/JOB_REQUIREMENTS.md): how each deliverable addresses the supplied position description.
- [Agent instructions](AGENTS.md): working rules, independence, priorities, and plain writing.
- [Presentation specification](docs/PRESENTATION_SPEC.md): a full 20-minute talk and required slide deliverables.
- [Presentation guide](docs/PRESENTATION_GUIDE.md): external guidance published in 2007–2014, with direct sources.
- [One-week plan](docs/PLAN.md): implementation and rehearsal schedule.
- [Research context](docs/RESEARCH_CONTEXT.md): public dataset and study background.

## Current status

The binary analysis, subtype follow-up, and shared prediction code are complete. The
[analysis report](results/analysis/20260915_baseline/REPORT.md) includes six charts
in PNG and editable SVG, model comparisons, individual error review, subtype and
assay-group summaries, uncertainty intervals, and score reliability. The
[viral-target review](results/analysis/20260915_viral/REPORT.md) examines the two
important BK measurements and study composition.

CatBoost missed 25 of 169 rejection cases and falsely flagged 8 of 176
no-rejection cases. Eighteen of its misses were T-cell-mediated rejection.
Sensitivity was 85.2% (95% specimen-bootstrap interval 79.7–90.7%). Its Brier
score was 0.078; agreement between scores and observed rejection fractions varies
across score ranges, so the application continues to return a **model score**.

Training and the batch prediction application use one
[shared package](docs/CODE_GUIDE.md). A new 27-model training run reproduced all
nine evaluation prediction tables exactly, including unchanged split assignments
and thresholds. The [comparison record](results/checks/20260915_shared/reproduction.json)
and [new run manifest](results/reproduction/20260915_shared/run_manifest.json)
preserve that evidence. The original baseline remains intact.

All [30 checks pass](results/checks/20260915_shared/tests.json), covering malformed
inputs, source joins, schema compatibility, prediction consistency, and analysis
failure cases. The shared CLI also reproduced all 345 primary evaluation scores
exactly after reloading the new model.

The [subtype follow-up](results/followup/20260915_subtypes/REPORT.md) compares
four-class CatBoost, multinomial logistic regression, and the separate component
models. Logistic regression correctly named 10 of 18 mixed diagnoses and
incorrectly called 5 other specimens mixed; the component models also named
10 mixed diagnoses but made 13 false mixed calls. The four-class models did not
improve the binary rejection error counts at their discovery-selected thresholds.
The service therefore keeps the original binary model.

The local FastAPI application serves a small demonstration page and the same
validated prediction code. See [the API guide](docs/API.md) for its request
contract and [software verification](docs/VERIFICATION.md) for the automated
checks and clean-install procedure.

The expanded suite has [55 passing tests](results/checks/20260915_application/checks.json).
The [real HTTP check](results/checks/20260915_application/http/http.json)
compared all 345 validation specimens with the CLI and saved predictions; the
largest score difference was `1.11e-16`, within the `1e-12` tolerance.
The [final clean installation](results/checks/20260915_application/fresh_setup_final.json)
also passed all 55 tests and verified the packaged page, API, and CLI in its own
environment. [Browser verification](results/checks/20260915_application/browser.json)
covers valid and invalid inputs, batch upload, and clearing results when inputs
or model details change.
The CI workflow runs on pushes and pull requests; local verification records
remain available alongside the hosted check results.

## Run the application

From this project's root:

```powershell
uv sync --frozen
uv run --frozen python scripts/prepare_demo.py
uv run --frozen uvicorn kidney_biopsy.api:app --host 127.0.0.1 --port 8765 --no-access-log
```

Open [the local demonstration](http://127.0.0.1:8765). Select a public example or
upload a compatible raw-count CSV. The page shows the model score, frozen
threshold, research flag, and observed false flags and misses. The invalid
example demonstrates what happens when a required assay target is missing.

The prepared examples live in ignored `data/demo/`. Preparation runs once; if
that directory already exists, start the server directly. To prepare a different
set, choose a new `--output-dir` and set `KIDNEY_BIOPSY_DEMO_DIR` accordingly.
The HTTP service accepts up to 16 specimens and 2 MiB per request. The CLI's
larger limits remain useful for batch analysis.

The default service model is the preserved binary classifier from
`results/reproduction/20260915_shared`. On a clean checkout, download the inputs
and train a new run using the commands below, then point both example preparation
and the service at that run:

```powershell
uv run --frozen python scripts/prepare_demo.py --results-dir "results/reproduction/$runName"
$env:KIDNEY_BIOPSY_RESULTS_DIR = "results/reproduction/$runName"
uv run --frozen uvicorn kidney_biopsy.api:app --host 127.0.0.1 --port 8765 --no-access-log
```

`GET /health` reports readiness, `GET /model` describes the input and model, and
`POST /predict` accepts a raw UTF-8 CSV body with `Content-Type: text/csv`.
Incoming counts are processed in memory and are not saved or logged.

## Run the analysis

Use Python 3.12 and uv. Run commands from this folder. Setup downloads packages;
subsequent runs use the local environment. The data downloader verifies existing
local files and only downloads missing inputs from their public source.

```powershell
uv sync --frozen
uv run python experiments/rejection_public/download.py
uv run python scripts/verify_local_data.py
$runName = Get-Date -Format 'yyyyMMdd-HHmmss'
uv run python experiments/rejection_public/run.py --output-dir "results/reproduction/$runName" --model-dir "data/processed/models/$runName"
uv run python -m kidney_biopsy --geo-validation --results-dir "results/reproduction/$runName" --output "data/processed/predictions/$runName.csv"
uv run python scripts/verify_inference.py --run-dir "results/reproduction/$runName" --inference-csv "data/processed/predictions/$runName.csv" --output "results/checks/$runName/inference.json"
uv run python scripts/analyze_results.py --run-dir "results/reproduction/$runName" --output-dir "results/analysis/$runName" --case-dir "data/processed/analysis/$runName"
uv run python -m unittest discover -s tests -v
```

The timestamp gives each run a new folder and preserves completed outputs.
To regenerate only the analysis, use `--run-dir results/reproduction/baseline`
with new analysis/case directories. The viral review is a separate reproducible
command:

```powershell
$reviewName = Get-Date -Format 'yyyyMMdd-HHmmss'
uv run python scripts/review_viral_targets.py --output-dir "results/analysis/$reviewName-viral" --specimen-dir "data/processed/analysis/$reviewName-viral"
```

To score a compatible raw-count CSV, replace `--geo-validation` with
`--counts-csv path/to/counts.csv`. The first column is the specimen identifier;
remaining columns must contain every required assay target, including the 12
housekeeping targets. Reordered targets are accepted; missing, duplicate, or extra
targets are rejected. Use a new output filename each time. The original
`experiments/rejection_public/predict.py` command delegates to this same package.
The module command above also avoids Windows restrictions on generated script
launchers.

## Reproduce the subtype comparison

The completed subtype run contains five candidates, saved discovery choices,
four-diagnosis confusion matrices, class sensitivity and precision with intervals,
mixed-rejection review, and comparisons with the frozen binary benchmark.
All model choices use discovery data. It is described as follow-up analysis
because the technical-validation cohort had already been examined.

To rerun against the populated project's preserved benchmark:

```powershell
$subtypeRun = Get-Date -Format 'yyyyMMdd-HHmmss'
uv run --frozen python experiments/rejection_subtypes/run.py --output-dir "results/followup/$subtypeRun" --model-dir "data/processed/models/$subtypeRun-subtypes" --case-dir "data/processed/analysis/$subtypeRun-subtypes"
```

For another locally trained benchmark, also set `--benchmark-run` and
`--benchmark-models` to its project-relative result and model directories.
The [report](results/followup/20260915_subtypes/REPORT.md) links to editable charts
and aggregate tables. Model binaries and specimen-level outputs stay ignored.

## Local files and version control

The two public assay inputs live in `data/raw/rejection_public/`, totaling about
16 MB. Their [source manifest](data/manifest.json) records public download URLs,
sizes, and hashes. Downloading a clean checkout requires internet access; the
populated project can train and predict from its own local inputs.

Models are trained here and stored in `data/processed/models/`. Raw data, processed
data, source-document copies, models, environments, and caches are Git-ignored.
Small reproducibility records, aggregate scores, and reports remain reviewable
under `results/`. Per-specimen splits and predictions remain local and Git-ignored. The complete supplied job-description text is included in
[local references](docs/references/JOB_DESCRIPTION.txt).

Every script resolves paths within this project. There are no dependencies on
another project, shared model files, or external Git history. The initialized Git
repository uses its own [GitHub remote](https://github.com/ca34525/Kidney-Biopsy-Rejection-Classifier).

## What the model means

The primary target is any recorded histological rejection versus no rejection.
The input must already have been measured using a compatible biopsy assay. The
project evaluates agreement with those labels and the false flags and missed
cases at a chosen threshold. It is a research demonstration, with no established
clinical benefit.
