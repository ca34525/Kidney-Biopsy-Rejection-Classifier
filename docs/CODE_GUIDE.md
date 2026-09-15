# Shared preprocessing and prediction

The research training script and batch prediction application import
`src/kidney_biopsy/`. The package owns the input checks, source readers,
housekeeping normalization, score calculation, and saved-model loading.
The training script keeps model fitting and discovery-based selection.

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
responsibility.

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

The FastAPI service and HTML demonstration are subsequent project work.
They can call the same package without copying preprocessing or importing
the training script.

## Development record: September 15, 2026

Codex assisted with extracting the package, writing the analysis and checks,
and reviewing generated charts. Acceptance evidence is the 30 passing tests,
the 109.7-second local rerun of the fixed 27-model procedure, exact agreement
across nine evaluation prediction tables, and exact agreement after model reload.
The existing discovery split, model candidates, selection rule, and thresholds
were preserved. The calibration and error reviews did not change model fitting.
