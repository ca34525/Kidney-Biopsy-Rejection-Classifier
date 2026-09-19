# Kidney biopsy rejection classifier

Can molecular measurements from an existing kidney biopsy classify
its recorded rejection diagnosis? This project compares models on public
NanoString B-HOT data and serves the selected model through a small research app.

The clinical motivation is a **molecular second opinion for uncertain transplant
biopsies**. RNA measurements could provide additional evidence when microscopic
findings are borderline or conflict with other clinical information. This tested,
reproducible prototype is an early step toward that use: it evaluates agreement
with recorded diagnoses and makes scoring available for further research. Its
added benefit in difficult cases remains to be evaluated. The
[research context](docs/RESEARCH_CONTEXT.md#why-a-molecular-second-opinion-could-be-useful)
records the supporting Banff guidance, B-HOT study, and related UNOS research.

Start with the [current status and reading order](docs/STATUS.md). It distinguishes
completed evidence, the frozen service, and the remaining presentation work.

## Result

All four comparisons use the same 345 technical-validation specimens and fixed
thresholds. Antibody-mediated, T-cell-mediated, and mixed rejection count as rejection.
The source dataset includes 1,193 transplant biopsies and 202 native-kidney
controls; validation includes 334 transplant biopsies and 11 native-kidney controls.
These results therefore describe the combined study population. The public
metadata do not identify the native-kidney specimens individually. See the
[September 19 source review](docs/references/STUDY_AUDIT_20260919.md).

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

The [presentation figures](results/presentation/20260917_evidence/README.md) show
the same error counts and score reliability with larger labels and editable text.

The output is a **model score**. This study measures agreement with recorded
diagnoses; it does not establish clinical benefit or reliable individual probabilities.
Patient and referring-center separation between cohorts is not documented; all
biopsies were processed at Arkana Laboratories. File validation does not establish
assay quality.

## Presentation

The draft includes [editable slides](presentation/unos_kidney_biopsy.pptx), a
[PDF backup](presentation/unos_kidney_biopsy.pdf), and the separate
[HTML speaking script](presentation/speaking_script.html). It has 19 main slides
and 8 backup slides, with 20 minutes of planned delivery. All spoken text is in
the HTML file; PowerPoint notes are empty. See the
[presentation guide](presentation/README.md) for source files and the demo fallback.
Full timed rehearsals remain pending.

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

**Follow the specimen** shows a public example's actual count normalization,
score, threshold, and agreement with its recorded diagnosis. It illustrates the
shared prediction path; diagnosis and specimen ID are not model inputs.

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
uv run --frozen ruff check src scripts tests experiments
uv run --frozen ruff format --check src scripts tests experiments
uv run --frozen python scripts/check_project.py
```

The [verification guide](docs/VERIFICATION.md) records tests, clean package
installation, and real HTTP/CLI agreement across all 345 validation specimens.
The [audit](docs/AUDIT.md) records the defensibility review, implementation fixes,
and remaining gaps. The GitHub Actions workflow also builds and checks a container
using a small synthetic model. The [current status](docs/STATUS.md#evidence-available)
links the verified hosted pass and identifies its revision. A cloud deployment
has not been performed.

## Run in Docker

In this populated folder, prepare the existing frozen model and public examples:

```powershell
uv run --frozen python scripts/prepare_container.py
```

After following the clean-checkout and demo steps above, use this preparation
command instead so the container includes your new run and its examples:

```powershell
uv run --frozen python scripts/prepare_container.py --results-dir "results/reproduction/$runName" --demo-dir "data/demo/$runName"
```

Preparation creates `build/container` and refuses to overwrite it. Reuse that
folder only for the same model and examples; the [container guide](docs/CONTAINERS.md#prepare-build-verify)
explains how to preserve an existing bundle before preparing another run.
Then build and start the image:

```powershell
docker build --platform linux/amd64 --tag kidney-biopsy:demo .
docker run --rm --publish 127.0.0.1:8000:8000 kidney-biopsy:demo
```

Open [the container demo](http://127.0.0.1:8000). See the [container guide](docs/CONTAINERS.md)
for the automated prediction check and an explanation of each file. The
[AWS guide](docs/AWS_DEPLOYMENT.md) gives the remaining steps to host that image
on a small Lightsail container service.

## Additional analysis

The [discovery-only stability study](results/followup/20260917_stability/REPORT.md)
selected CatBoost in 13 of 20 repetitions and logistic regression in 7. Model
choice changed with the development split, leaving logistic regression a credible
simpler alternative. These overlapping repetitions are descriptive follow-up
evidence; the frozen service and original validation results are unchanged.

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

The [current reading order](docs/STATUS.md) links results, checks, and project
background. [Next steps](docs/NEXT_STEPS.md) records deferred research and product
ideas. The [source manifest](data/manifest.json) records public input URLs and hashes.

The two raw assay inputs total about 16 MB. Data, models, specimen-level outputs,
environments, and caches stay local and Git-ignored. Aggregate results and reports
are tracked under `results/`. This folder has its own inputs, training runs,
lockfile, and environment; it does not depend on another project.
