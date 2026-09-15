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

The specifications and first independent training run are complete. This folder trained
27 models from local raw inputs, then reproduced all 345 evaluation scores exactly
from the saved model. See the [fresh results](results/reproduction/baseline/REPORT.md).
The API, demonstration page, container, CI workflow, and slide deck are specified
future work.

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
uv run python experiments/rejection_public/predict.py --geo-validation --results-dir "results/reproduction/$runName" --model-dir "data/processed/models/$runName" --output "results/reproduction/$runName/inference.csv"
uv run python scripts/verify_inference.py --run-dir "results/reproduction/$runName" --inference-csv "results/reproduction/$runName/inference.csv"
```

The timestamp gives each run a new folder and preserves completed outputs.
To check the existing baseline without retraining, run
`uv run python scripts/verify_inference.py`. To score a compatible raw-count CSV, replace
`--geo-validation` with `--counts-csv path/to/counts.csv`. The first CSV column is
the specimen identifier; the remaining columns include every required assay target,
including the 12 housekeeping targets.

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
repository has no remote.

## What the model means

The primary target is any recorded histological rejection versus no rejection.
The input must already have been measured using a compatible biopsy assay. The
project evaluates agreement with those labels and the false flags and missed
cases at a chosen threshold. It is a research demonstration, with no established
clinical benefit.
