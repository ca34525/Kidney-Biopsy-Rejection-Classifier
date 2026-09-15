# Kidney biopsy rejection classifier

Can molecular measurements from an existing kidney transplant biopsy classify
its recorded rejection diagnosis? This project compares models on public
NanoString B-HOT data and serves the selected model through a small research app.

## Result

All four comparisons use the same 345 technical-validation specimens and fixed
thresholds. Antibody-mediated, T-cell-mediated, and mixed rejection count as rejection.

| Model | Missed rejection / 169 | False flags / 176 |
| --- | ---: | ---: |
| CatBoost | 25 | 8 |
| Multivariable logistic regression | 33 | 8 |
| IFNG alone | 14 | 75 |
| Training constant | 0 | 176 |

CatBoost won the discovery-screen comparison by one fewer false flag than
logistic regression; both detected 157 of 174 rejection cases. Its advantage over
logistic regression remains uncertain. The experimental 90% screening sensitivity
target was not maintained in technical validation: CatBoost detected 85.2%.
See the [analysis report](results/analysis/20260915_baseline/REPORT.md) for thresholds,
uncertainty intervals, error review, and editable charts.

The output is a **model score**. This study measures agreement with recorded
diagnoses; it does not establish clinical benefit, reliable individual probabilities,
or patient/center independence. File validation does not establish assay quality.

## Run the demo

Use Python 3.12 and uv. Run all commands from this project's root. In this populated
folder, the data and frozen model are already available:

```powershell
uv sync --frozen
uv run --frozen uvicorn kidney_biopsy.api:app --host 127.0.0.1 --port 8765 --no-access-log
```

Open [the local demo](http://127.0.0.1:8765). Choose a public specimen or upload
raw counts, then try the incomplete-file example. The page shows the score,
threshold, research flag, and observed error counts. Uploads are processed in
memory and are not saved or logged.

If examples have not been prepared, run `uv run --frozen python scripts/prepare_demo.py`
once before starting the server. Requests accept at most 16 specimens and 2 MiB.
The [API guide](docs/API.md) covers the CSV format, routes, configuration, and errors.

## Reproduce from a clean checkout

The downloader verifies existing local inputs and downloads only missing files.
Each run gets a new directory; completed results are preserved.

```powershell
uv sync --frozen
uv run --frozen python experiments/rejection_public/download.py
uv run --frozen python scripts/verify_local_data.py
$runName = Get-Date -Format 'yyyyMMdd-HHmmss'
uv run --frozen python experiments/rejection_public/run.py --output-dir "results/reproduction/$runName" --model-dir "data/processed/models/$runName"
uv run --frozen python -m kidney_biopsy --geo-validation --results-dir "results/reproduction/$runName" --output "data/processed/predictions/$runName.csv"
uv run --frozen python scripts/verify_inference.py --run-dir "results/reproduction/$runName" --inference-csv "data/processed/predictions/$runName.csv" --output "results/checks/$runName/inference.json"
uv run --frozen python scripts/analyze_results.py --run-dir "results/reproduction/$runName" --output-dir "results/analysis/$runName" --case-dir "data/processed/analysis/$runName"
```

To use that new run in the demo:

```powershell
uv run --frozen python scripts/prepare_demo.py --results-dir "results/reproduction/$runName" --output-dir "data/demo/$runName"
$env:KIDNEY_BIOPSY_RESULTS_DIR = "results/reproduction/$runName"
$env:KIDNEY_BIOPSY_DEMO_DIR = "data/demo/$runName"
uv run --frozen uvicorn kidney_biopsy.api:app --host 127.0.0.1 --port 8765 --no-access-log
```

For a raw-count CSV, replace `--geo-validation` with `--counts-csv path/to/counts.csv`.
The first column holds specimen IDs; the other columns must contain all 770 assay
targets. Target order may change. Missing, duplicate, or extra targets fail clearly.
The CLI supports larger batches than the HTTP service.

## Read the code

The prediction path is short:

```text
CSV → validate counts → normalize with 12 housekeeping targets → frozen model → score and flag
```

Training and the API use the same preprocessing and prediction package. Model
fitting stays in the research scripts; the app serves one HTML page with plain
JavaScript and CSS. See the [code guide](docs/CODE_GUIDE.md) for the reading order,
responsibilities, and model checks.

## Check the software

```powershell
uv run --frozen python scripts/check_project.py
```

The [verification guide](docs/VERIFICATION.md) records tests, clean package
installation, and real HTTP/CLI agreement across all 345 validation specimens.
The [audit](docs/AUDIT.md) records the defensibility review, implementation fixes,
and remaining gaps. The GitHub Actions workflow is configured; a hosted pass,
local container run, and cloud deployment need their own execution evidence.

## Additional analysis

The [subtype follow-up](results/followup/20260915_subtypes/REPORT.md) compares four-class
models and separate rejection components. It did not justify replacing the binary
service model. The [viral-target review](results/analysis/20260915_viral/REPORT.md)
examines BK measurements and study composition. To rerun them against the preserved
local benchmark, use new destinations:

```powershell
$followup = Get-Date -Format 'yyyyMMdd-HHmmss'
uv run --frozen python experiments/rejection_subtypes/run.py --output-dir "results/followup/$followup" --model-dir "data/processed/models/$followup-subtypes" --case-dir "data/processed/analysis/$followup-subtypes"
uv run --frozen python scripts/review_viral_targets.py --output-dir "results/analysis/$followup-viral" --specimen-dir "data/processed/analysis/$followup-viral"
```

For another binary run, the subtype script accepts `--benchmark-run` and
`--benchmark-models`. The viral review accepts `--baseline-dir`.

## Project records

| Read | Contents |
| --- | --- |
| [Project specification](docs/PROJECT_SPEC.md) | Question, data, evaluation, and required deliverables |
| [Research context](docs/RESEARCH_CONTEXT.md) | Dataset and source-study methods |
| [Plan](docs/PLAN.md) | Completed work and remaining delivery tasks |
| [Presentation specification](docs/PRESENTATION_SPEC.md) and [guide](docs/PRESENTATION_GUIDE.md) | Full 20-minute talk, slides, notes, and rehearsal |
| [Source manifest](data/manifest.json) | Public download URLs, sizes, and hashes |

The two raw assay inputs total about 16 MB. Data, models, specimen-level outputs,
environments, and caches stay local and Git-ignored. Aggregate results and reports
are tracked under `results/`. This folder has its own inputs, training runs,
lockfile, and environment; it does not depend on another project.
