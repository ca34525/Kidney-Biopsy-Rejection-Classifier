# Shared preprocessing and prediction

For the illustrated, detailed version, open the
[code guide](CODE_GUIDE.html) in a browser. Its six
workflows pair script/function diagrams with explanations, source and test links,
one real public specimen, maintenance scenarios, and exercises. The
[editable guide sources](code_guide/README.md) include a rebuild and reference check.

The research training script and batch prediction application import
`src/kidney_biopsy/`. The package owns the input checks, source readers,
housekeeping normalization, score calculation, and saved-model loading.
The training script keeps model fitting and discovery-based selection.

See [current status](STATUS.md) for the latest evidence. The CLI and API default
to the same frozen `results/reproduction/20260915_shared` run. Both respect
`KIDNEY_BIOPSY_PROJECT_ROOT` and `KIDNEY_BIOPSY_RESULTS_DIR`; explicit CLI options
override those environment settings.

## Reading order

Start with the path a single prediction takes:

1. [CLI](../src/kidney_biopsy/cli.py): load the configured model, read a CSV, write results.
2. [Preprocessing](../src/kidney_biopsy/preprocessing.py): check the complete batch and normalize each specimen.
3. [Prediction](../src/kidney_biopsy/prediction.py): check model compatibility, calculate scores, apply the threshold.
4. [API](../src/kidney_biopsy/api.py): expose that same path over HTTP.

The [public-specimen walkthrough](API.md#follow-the-specimen) makes this path
visible in the browser. It shows real IFNG and housekeeping values from a verified
prepared example, then uses the same predictor and compares its flag with the
recorded label. It does not add a feature-explanation model or a second scoring path.

Then read `run_experiment` in [training](../experiments/rejection_public/run.py).
It calls `prepare_data`, `fit_candidates`, and `freeze_and_evaluate` in that order.
The output directories are passed explicitly. The source reader is only needed
to understand the public-study import. Historical source snapshots under
`results/` explain old runs; they are not additional application implementations
to maintain.

For reporting, `analyze_run` in [analysis](../scripts/analyze_results.py) shows the
sequence from verified inputs through calculations, tables, figures, and the
manifest. Each figure has a named plotting function. The browser script likewise
separates the prediction request from single-specimen and batch rendering.

## Input contract

A CSV contains one specimen per row. The first column contains a unique,
nonempty specimen ID. Remaining columns must contain the frozen model's
758 assay targets and all 12 housekeeping targets. Target names must match
exactly, including spaces and punctuation. Column order may change.

The shared reader rejects empty input, duplicate IDs or target names,
missing or extra targets, malformed rows, nonnumeric counts, negative
counts, and non-finite values. Extra columns, including metadata, are
rejected. A batch fails as a whole if any specimen is invalid. The default
CSV batch limit is 1,000 specimens and the CLI file limit is 20 MiB. Numeric checks do not establish that
the input came from the correct assay; assay compatibility is the caller's
responsibility. These are file and numeric checks; the caller must also complete
the laboratory's assay quality checks.

Each specimen is transformed independently:

```text
log2(target count + 1) - mean(log2(housekeeping count + 1))
```

The mean uses the same 12 named housekeeping targets in training and
prediction. Housekeeping targets are then removed, and predictors are
ordered using the frozen schema. Learned scaling and feature selection
remain inside fitted model pipelines and are fitted on training rows only.

## Package responsibilities

| Code | Responsibility |
| --- | --- |
| `preprocessing.py` | Validate counts and labels, read CSVs, define the versioned assay schema, normalize counts |
| `source.py` | Read GEO metadata and raw RCC counts; reject broken specimen joins and duplicate targets |
| `prediction.py` | Verify configured model artifacts and schema, calculate scores, apply the frozen threshold |
| `cli.py` | Handle batch prediction arguments and write results using the shared predictor |
| `experiments/rejection_public/run.py` | Fit the fixed candidates, select models and thresholds using discovery, save evaluation and provenance |

The application's output is a **model score** and a research flag. The
threshold was selected for screening sensitivity; it is not a probability
calibration procedure. See the analysis report for the observed reliability
of these scores.

## Model compatibility and provenance

Load a configured local training run through `load_predictor`, then call
the returned predictor's `predict(counts)` method with raw counts. Both
training and prediction use `predict_scores` for model scoring. There is
no request-supplied model-loading path.

The loader checks the model and frozen metadata against the run manifest
before loading the project-controlled artifact. It also checks feature
names and order, binary classes, preprocessing/schema versions, and the
threshold. A joblib file must come from this trusted local workflow;
hashes detect accidental changes and are not a signature from an external
authority.

New training runs preserve source snapshots, the environment lockfile,
explicit configuration, input hashes, actual split assignments, fitted
comparison models, and screening/evaluation predictions. Completed runs
are never reused as output directories. `scripts/verify_reproduction.py`
compares assignments, selected models, thresholds, and scores with a
preserved reference run; its score tolerance is `1e-12`.

The FastAPI service in `api.py` calls this package without copying preprocessing
or importing the training script. It serves the standalone page in `static/`.
The [API guide](API.md) describes startup, example preparation, request limits,
and structured errors. The service uses the frozen binary model; the separate
four-class follow-up is a research comparison in `experiments/rejection_subtypes/`.

The [verification guide](VERIFICATION.md) covers the test suite, CI, and a fresh
noneditable installation. `scripts/verify_http_service.py` starts a real local
server and compares all 345 validation predictions with the CLI and saved scores.

The [container guide](CONTAINERS.md) explains the deployment path: verify and copy
the serving artifacts, build the image, then check a running service against the
local model. Its file table is the reading order for that work. CI uses the same
path with a tiny synthetic CatBoost model; the real deployment image contains the
selected research model and prepared public examples.

## Development record: September 15, 2026

The counts below describe those completed checks. The [verification guide](VERIFICATION.md)
records subsequent checks; the older totals are not the current suite size.

Codex assisted with extracting the package, writing the analysis and checks,
and reviewing generated charts. Acceptance evidence is the 30 passing tests,
the 109.7-second local rerun of the fixed procedure (27 fits: nine configurations
for each of three binary targets), exact agreement
across nine evaluation prediction tables, and exact agreement after model reload.
The existing discovery split, model candidates, selection rule, and thresholds
were preserved. The calibration and error reviews did not change model fitting.

The subsequent subtype comparison fitted five candidates in 117.3 seconds. Codex
also assisted with the API, example preparation, browser behavior, and automated
verification. The expanded suite has 55 passing tests. A real HTTP check compared
all 345 validation specimens with CLI and saved predictions within `1e-12`.
Browser checks covered a valid example, invalid input, a two-specimen upload,
clearing stale results after input changes, and refusing results if the configured
model changed while the page remained open. The fresh-install record in the
verification guide establishes that the packaged app works in a separate local
environment. These are software checks, not new clinical validation.
