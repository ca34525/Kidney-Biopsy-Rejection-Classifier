# Analysis notebooks

Three executable notebooks explain the data, the completed model comparison, and
the RNA measurements that contribute to model scores. They were added September 27,
2026, after the presentation. They use this project's own raw data and fitted
models. New plots are retrospective descriptions.

## Read in order

| Notebook | What it shows |
| --- | --- |
| [1. Data quality and preprocessing](01_data_quality_and_preprocessing.ipynb) | Missingness, duplicate records, invalid counts, unusual specimens, housekeeping targets, and a worked normalization |
| [2. Exploratory data analysis](02_exploratory_data_analysis.ipynb) | Diagnosis composition, RNA distributions, correlation, PCA, assay batches, cohort differences, and BK viral signals |
| [3. Models and RNA contributions](03_model_comparison_and_rna_contributions.ipynb) | Model recipes, screening thresholds, same-row errors, uncertainty, score reliability, CatBoost importance, SHAP, logistic coefficients, and individual predictions |

The checked-in notebooks contain executed tables and figures, so they can be read
without downloading data or installing Jupyter. The
[execution record](../results/notebooks/20260927_eda_reviewed/execution.json) identifies the
run. Browser views and editable SVG figures are in that same result directory.

The sequence follows the data preparation → EDA → modeling organization in
[TexasReadmissionRiskAPI](https://github.com/ca34525/TexasReadmissionRiskAPI/tree/main/notebooks),
reviewed September 27, 2026. The analytical code and results belong to this project.

## Open and run interactively

From this project's root:

```sh
uv sync --frozen --group notebooks
uv run --frozen --group notebooks jupyter lab notebooks
```

Select the kernel from this project's `.venv` if your editor offers multiple Python
environments. Each notebook runs independently with **Restart Kernel and Run All**;
no variables or generated tables carry over from another notebook.

Notebook dependencies are optional; the prediction service does not require them.
If Windows application control blocks uv's temporary build Python, the existing
project Python can build the package:

```sh
uv pip install setuptools
uv sync --frozen --group notebooks --no-build-isolation
```

## Execute and export all three

```sh
uv run --frozen --group notebooks python scripts/run_notebooks.py
```

The runner uses this environment's Python in a separate fresh kernel for each
notebook. It creates a timestamped directory under `results/notebooks/`, containing:

- Executed notebook copies and HTML views.
- Aggregate JSON tables and PNG/SVG figures.
- Input hashes, model version, settings, source hashes, and output hashes.
- Source notebook snapshots and an execution record.

An explicit destination must be new:

```sh
uv run --frozen --group notebooks python scripts/run_notebooks.py --output-dir results/notebooks/my_review
```

The default model run is `results/reproduction/20260915_shared`, whose artifacts
are present in this populated checkout. Existing results and model files are never
overwritten. An interactive run also creates a new output directory each time
the setup cell runs.

## Reproduce from a clean checkout

Raw data, saved split/prediction CSVs, and model binaries are Git-ignored. A fresh
clone must download the public inputs and reproduce a run before executing notebooks
2 and 3. Notebook 1 only requires the public inputs.

```sh
uv sync --frozen --group notebooks
uv run --frozen --group notebooks python experiments/rejection_public/download.py
uv run --frozen --group notebooks python scripts/verify_local_data.py
uv run --frozen --group notebooks python experiments/rejection_public/run.py --output-dir results/reproduction/notebook_reproduction --model-dir data/processed/models/notebook_reproduction
uv run --frozen --group notebooks python scripts/run_notebooks.py --run-dir results/reproduction/notebook_reproduction
```

Use new training/model directories for later reproductions. To select a reproduced
run in an interactive notebook, set `KIDNEY_BIOPSY_NOTEBOOK_RUN` to that
project-relative run directory before creating `NotebookSession`.

Notebook 3 explicitly checks that the selected model is the depth-4 CatBoost model
explained here. A different winning model requires adapting the interpretation,
not silently attaching these charts to it. Cross-platform scores can differ slightly;
checks compare each run to its own saved predictions, with absolute tolerance 1e-10.

## Interpretation

EDA does not remove specimens or retune the preserved models. PCA and its scaler
are fitted on training specimens only. CatBoost SHAP rankings use all 263 screening
specimens, and explain the model in log-odds units. Contributions are not causal
effects or calibrated probabilities. The BK targets are viral measurements.

Full specimen tables and SHAP matrices remain in memory. Displayed count snippets
and four prediction examples omit accession IDs. Aggregate exports are tracked;
there is no export of the complete specimen-level data.

The code for loading, validation, normalization, and scoring is shared with the
application. `notebook_support.py` handles paths, artifact verification, and output
records; analytical calculations remain visible in notebook cells.
