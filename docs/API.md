# Local research application

The application scores raw B-HOT counts with the frozen binary model from
`results/reproduction/20260915_shared`. It uses the same `Predictor`, CSV reader,
and housekeeping normalization as the command-line prediction path. The subtype
follow-up does not replace this model or its threshold.

## Start the demonstration

Run from this project's root after setting up the environment and generating the
shared reproduction run described in the README. If `data/demo/` already exists,
skip the example-preparation command:

```powershell
uv sync --frozen
uv run --frozen python scripts/prepare_demo.py
uv run --frozen uvicorn kidney_biopsy.api:app --host 127.0.0.1 --port 8765 --no-access-log
```

Open `http://127.0.0.1:8765` in a browser. Select a public example, choose **Get
research score**, and then **Try an incomplete file** to see a missing-target error.
An upload uses the chosen file; selecting another public example clears that upload.
For multi-specimen uploads, every result appears in a table. Changing the input
clears the previous result. If the configured server model changes while the page
is open, the page refuses the mismatched result and asks for a reload so the
score, threshold, and evaluation counts stay consistent.

### Follow the specimen

For a prepared public example, **Follow the specimen** shows the actual IFNG raw
count, its `log2(count + 1)`, the mean of the 12 housekeeping log counts, and the
subtraction used to obtain its normalized value. Expand **See the 12 housekeeping
measurements** to inspect that mean. The same operation produces all 758 model
inputs; IFNG is one arithmetic example, not an explanation of the full model's
decision.

The walkthrough then shows the model score, frozen threshold, research flag,
and agreement with the specimen's recorded diagnosis. The diagnosis and specimen
ID are not predictors. This is a discovery-screen example; the displayed
evaluation error counts describe the separate author technical-validation cohort.
The route accepts only prepared, valid public examples and rechecks their file,
specimen, and model identity. Uploaded files use the ordinary prediction path.

Example preparation verifies the raw source manifest and saved split before
writing five CSV files and a provenance manifest under ignored `data/demo/`. Four
valid examples are the first accessions in lexical order within each recorded
diagnosis in the discovery-screen split. Their scores did not guide selection.
The invalid example removes IFNG from the no-rejection example. Example preparation
refuses to overwrite an existing directory; reuse prepared files or supply a new
`--output-dir`. Serving examples rechecks their file hashes.

The page shows the model's own verified technical-validation results: 8 false
rejection flags among 176 specimens recorded as no rejection, and 25 missed
rejection cases among 169 recorded as rejection. These counts are loaded from the
same run's hash-verified `biopsy_results.json`; they are not fixed to the page or
substituted for another configured model. The displayed threshold is rounded;
the actual decision always uses the full frozen value, `0.8765880870219778`.

## Process configuration

| Setting | Default | Meaning |
| --- | --- | --- |
| `KIDNEY_BIOPSY_PROJECT_ROOT` | `.` | Project root containing the selected run and model |
| `KIDNEY_BIOPSY_RESULTS_DIR` | `results/reproduction/20260915_shared` | Project-relative completed training run |
| `KIDNEY_BIOPSY_DEMO_DIR` | `data/demo` | Project-relative prepared example directory |

Paths to models come from the configured run's trusted manifest. Model and frozen
metadata hashes are checked before deserialization. Request parameters cannot
select a model. The service loads once at startup and reports unavailable if the
artifact is missing, modified, or incompatible with its schema; restart after
repairing the configured artifacts. Optional example or evaluation files may be
absent without preventing prediction.

Startup failures log a fixed error category, without specimen values or artifact
paths. The browser continues to receive the same concise unavailable response.

The application neither writes uploaded counts to files nor logs their contents.
The launch command disables HTTP access logs. It sends `Cache-Control: no-store`
for results and examples. Bind to localhost for the demonstration. No cloud
deployment is established by these local checks.

## API contract

| Route | Response |
| --- | --- |
| `GET /health` | 200 with `status: ready` and `model_loaded: true`, or 503 when the configured model is unavailable |
| `GET /model` | Target, version, schema, required targets, frozen threshold, input limits, and verified aggregate evaluation when available |
| `POST /predict` | Raw UTF-8 CSV body with `Content-Type: text/csv`; returns one versioned prediction per specimen |
| `GET /demo/examples` | Prepared public example labels and IDs; an empty list if examples have not been prepared |
| `GET /demo/examples/{id}` | One allowlisted prepared public CSV, checked against its manifest |
| `GET /demo/walkthrough/{example_id}` | Verified public example, IFNG normalization arithmetic, 12 housekeeping measurements, prediction, and recorded diagnosis |

`POST /predict` accepts at most **16 specimens** and **2 MiB** of uncompressed
UTF-8 text. The actual streamed body size is checked even if Content-Length is
missing or incorrect. `application/csv` is also accepted; JSON and multipart
uploads are not accepted. The route has no query parameters.

The first CSV column contains specimen IDs; all remaining columns are raw assay
counts. Include exactly the required targets returned by `/model`, including all
12 housekeeping targets. Reordering target columns is accepted. Missing or
duplicate targets, duplicate or empty specimen IDs, extra metadata or targets,
empty/ragged/malformed CSV, and nonnumeric, negative, or non-finite counts fail
the entire batch. No missing values are filled and no partial predictions are
returned. The caller must establish that counts came from the compatible assay.
File and numeric checks do not establish assay quality. The application assumes
the laboratory has completed its assay quality checks; this project did not
independently repeat control-probe or imaging QC for the deposited cohort.

Send a prepared valid example from PowerShell:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8765/predict -Method Post -ContentType 'text/csv' -InFile data/demo/no-rejection.csv
```

Or use curl:

```sh
curl -H 'Content-Type: text/csv' --data-binary @data/demo/no-rejection.csv http://127.0.0.1:8765/predict
```

A successful response contains `predictions` and `input_checks`. Each prediction
has `specimen`, `rejection_score`, `rejection_flag`, `threshold`, `model_version`,
`schema_version`, and `input_check: passed`. The flag is true when the score is
greater than or equal to the frozen threshold. The numeric output is labeled a
model score, not a verified probability for an individual biopsy.

For the incomplete example, the API returns HTTP 422:

```json
{
  "error": {
    "code": "invalid_csv",
    "message": "Missing required assay targets: IFNG"
  }
}
```

Other handled errors use the same structure: 400 for unsupported request
parameters or invalid Content-Length; 413 for excessive body size; 415 for an
unsupported content type or compression; and 503 for unavailable scoring.
Responses do not include raw counts, invalid specimen IDs, internal model paths,
or tracebacks.

## Verification

```powershell
uv run --frozen python -m unittest discover -s tests -p test_api.py -v
```

The self-contained API tests train a tiny synthetic model in a temporary folder.
They check API/CLI/direct prediction agreement at absolute tolerance `1e-12`,
column reordering, rejection of malformed batches, announced and streamed upload
limits, absence of output files, unavailable artifacts, incompatible schema,
trusted model selection, safe scoring failure, and example integrity checks.
They do not require downloaded study data or copy fitted models from elsewhere.

Application startup follows FastAPI's documented
[lifespan pattern](https://fastapi.tiangolo.com/advanced/events/). Tests run the
client as a context manager so startup and shutdown execute, following
[FastAPI's testing guidance](https://fastapi.tiangolo.com/advanced/testing-events/).
