# Clone setup and desktop comparison

Completed September 22, 2026 UTC (September 21 in America/Chicago).
Starting revision: `ccbaf31abcaa049be946efe849b7d2f243378976`.
Machine: macOS, Apple Silicon. The checkout was clean before setup.

The local research workflow and application now work. The main model choices and
validation error counts reproduce the committed desktop results. This is **not
an exact reproduction of every number or artifact**: the strict audit records
eight failed aggregate-file comparisons, and the original per-specimen predictions
were not committed.

[Every CLI command, including inspections and failed commands](COMMANDS.md) is
recorded separately. The local-only `command_log.json` includes the output
returned by the execution tools; some long outputs were truncated. It is
Git-ignored because the diagnostics include machine-specific paths.
File edits were made with the apply_patch tool, not an unrecorded shell command.

This branch preserves the aggregate reports, figures, run manifests, source
snapshots and verification records. Per the user's Git policy, new CSVs remain
ignored, including the aggregate tables linked from these reports. Those links
work in the populated laptop checkout; a fresh clone must regenerate the CSVs
with the recorded commands. Raw data, fitted models, demo files and the local
environment also remain ignored. Pushing the branch is not a backup of those
local artifacts. The [laptop presentation plan](../../../docs/MAC_PRESENTATION_PLAN.md)
records the freeze and remaining presentation work.

## What was restored

- Installed uv 0.12.17 into ignored `.uv-cache/bin`, without changing shell
  startup files. uv found the existing Homebrew Python 3.12.13 interpreter.
- Created this project's `.venv` and installed 39 packages from the unchanged
  `uv.lock`. The six modeling package versions and Python version match both
  desktop run manifests.
- Downloaded the two public GEO files into `data/raw/rejection_public`.
  Their sizes and SHA-256 hashes match `data/manifest.json` exactly.
- Trained 27 primary candidates, five subtype candidates, and 100 stability
  candidates. No fitted model, score, or completed analysis was copied from
  another project.
- Regenerated the primary report with 2,000 paired bootstrap replicates and its
  charts, subtype and stability reports, viral-target review, model artifacts,
  CLI predictions, and five demo files.
- Prepared `build/container` from this new model and examples.
- Added local shell helpers under ignored `data/processed/setup/20260922_mac_clone`.
  They select the new run explicitly; the original default points to a desktop
  model whose binary is absent from a clone.

New results live under:

| Work | Results | Local ignored artifacts |
| --- | --- | --- |
| Primary, 27 fits | `results/reproduction/20260922_mac_clone` | `data/processed/models/20260922_mac_clone` |
| Primary report | `results/analysis/20260922_mac_clone` | `data/processed/analysis/20260922_mac_clone` |
| Subtypes, 5 fits | `results/followup/20260922_mac_clone_subtypes` | Matching names under `data/processed/models` and `data/processed/analysis` |
| Stability, 100 fits | `results/followup/20260922_mac_clone_stability` | `data/processed/stability/20260922_mac_clone` |
| Viral review | `results/analysis/20260922_mac_clone_viral` | `data/processed/analysis/20260922_mac_clone_viral` |
| Examples | — | `data/demo/20260922_mac_clone` |

The primary, subtype and stability manifests record 44.3, 48.1 and 242.6 seconds
respectively for their workflows. These durations are not reproduction criteria.

## Main commands actually run

Commands were run from the project root in zsh. These are the principal commands;
the complete command transcript includes installation, all checks and follow-ups.
Completed output directories refuse overwriting, so choose a new name when
repeating a training or analysis command.

```sh
UV_UNMANAGED_INSTALL="$PWD/.uv-cache/bin" sh .uv-cache/bootstrap/install-uv.sh
UV_PYTHON_INSTALL_DIR="$PWD/.uv-cache/python" .uv-cache/bin/uv sync --frozen --python 3.12.13
.venv/bin/python experiments/rejection_public/download.py
.uv-cache/bin/uv run --frozen python scripts/verify_local_data.py

MPLCONFIGDIR=.uv-cache/matplotlib .uv-cache/bin/uv run --frozen python experiments/rejection_public/run.py --output-dir results/reproduction/20260922_mac_clone --model-dir data/processed/models/20260922_mac_clone

.uv-cache/bin/uv run --frozen python -m kidney_biopsy --geo-validation --results-dir results/reproduction/20260922_mac_clone --output data/processed/predictions/20260922_mac_clone.csv

MPLCONFIGDIR=.uv-cache/matplotlib .uv-cache/bin/uv run --frozen python scripts/analyze_results.py --run-dir results/reproduction/20260922_mac_clone --output-dir results/analysis/20260922_mac_clone --case-dir data/processed/analysis/20260922_mac_clone

.uv-cache/bin/uv run --frozen python scripts/prepare_demo.py --results-dir results/reproduction/20260922_mac_clone --output-dir data/demo/20260922_mac_clone

.uv-cache/bin/uv run --frozen ruff check src scripts tests experiments
.uv-cache/bin/uv run --frozen ruff format --check src scripts tests experiments
MPLCONFIGDIR=.uv-cache/matplotlib .uv-cache/bin/uv run --frozen python scripts/check_project.py --output results/checks/20260922_mac_clone/checks_after_path_fix.json
```

The installer was downloaded from `https://astral.sh/uv/install.sh` with curl
before execution. The first curl attempt failed because sandbox networking could
not resolve the host. The network-enabled retry succeeded. Downloads used the
existing public source URLs; the input manifest was not edited.

## What the comparison establishes

[The audit script](compare_desktop.py) checks committed evidence against the new
run. Its [full JSON result](desktop_comparison.json) keeps the fixed absolute
tolerance of `1e-12`, with no relative tolerance; it excludes runtime fields only.
It exits nonzero because the complete comparison does not pass. This failure is
preserved rather than relabeled as a success.

1. **Identical raw inputs:** 2,444,946 bytes for the series matrix and 13,547,520
   bytes for the raw archive; 15,992,466 bytes total. Both SHA-256 hashes match.
   A second downloader invocation verified the cached files without downloading.
2. **Identical assignments and metadata:** regenerated `biopsy_split.csv` and
   `raw_batch_identifiers.csv` match the original hashes after converting LF
   line endings to CRLF in memory. No saved file was changed for this comparison.
   The split contains 787 training, 263 screening and 345 validation specimens.
   Hash equality establishes the same row contents, labels and assignments.
3. **Same selected models:** all three selected models, ordered features, cohort
   sizes and available schema fields agree. Selected thresholds differ by at most
   `4.44e-16`. The current configuration and data-audit JSON agree with the
   desktop shared-code run.
4. **Same validation counts:** [30 count comparisons](validation_counts.json)
   agree exactly: all five recorded comparison entries for each of three targets,
   against both the original baseline and the shared-code desktop run.
   All numerical evaluation metrics in the shared-code results agree within
   `3.35e-13`, excluding elapsed time.
5. **Primary report reproduced numerically:** all eight aggregate CSV tables and
   the metrics JSON agree within `1e-12`. This includes error review, reliability
   bins, paired comparisons and uncertainty intervals. Images and report prose
   were not required to match byte for byte.
6. **Follow-up conclusions retained:** all subtype confusion matrices and error
   counts match. All 20 stability selections match (CatBoost 13, logistic 7), as
   do assessment error counts. All six viral-review CSVs agree within the strict
   tolerance.
7. **Original evidence preserved:** all 25 available artifacts listed across the
   two reference run manifests match their recorded hashes. Missing original
   binaries and specimen tables remain missing from those historical directories;
   newly generated files are in separate directories. All 55 artifacts in the
   new primary run also pass their own manifest checks.

| Main validation model | Missed rejection / 169 | False flags / 176 |
| --- | ---: | ---: |
| CatBoost | 25 | 8 |
| Logistic regression | 33 | 8 |
| IFNG | 14 | 75 |
| Constant | 0 | 176 |

## Differences and limits

The audit passes **29 of 37 aggregate-file comparisons**, plus all six
selected-model metadata comparisons. The eight failed file comparisons are:

- The oldest baseline results file records undefined constant-model predictive
  values as zero. The existing current code records them as null. The desktop
  shared-code run already uses the corrected representation; this was not a
  modeling change made during setup.
- Both historical screening tables differ for ExtraTrees. For its
  antibody-mediated-component candidate, false flags increased from 11 to 12.
  Thresholds and ranking metrics also differ for the ExtraTrees candidates.
  None was selected in either run.
- Two subtype tables contain small numeric differences beyond `1e-12`;
  the largest is about `1.67e-10`. Their error counts remain the same.
- Stability screening, assessment and summary tables contain numeric
  differences. An unselected depth-6 CatBoost candidate in repetition 6 has a
  threshold difference of about `0.00110946`; its screening ranking metrics
  also differ. Other differences include logistic thresholds. All final
  repetition selections and assessment error counts match.

[Discrepancies with row identities and both values](discrepancies.json) are
recorded explicitly. The environment has different native platform libraries
from the original desktop environment; platform effects are a possible
explanation, but their cause was not isolated here. No tuning, altered seeds,
larger tolerance, or changes to training were used to force agreement.

None of the regenerated prediction tables matched the desktop prediction hashes,
even after trying both newline conventions. Without the original specimen-level
tables, hashes cannot tell us how large those individual score differences are
or prove that exactly the same individual specimens received each flag.
A direct numeric comparison would require those original tables, or a desktop
comparison against this new run. Matching aggregate counts alone does not prove
that stronger claim.

The old `scripts/verify_reproduction.py` expects the original ignored artifacts
to be present and verifies their hashes before comparing rows. It therefore
cannot perform its usual desktop-to-rerun check in a plain clone. The separate
audit here makes that missing evidence explicit.

## Software checks and the one code edit

- Ruff check and format check pass for 36 Python files.
- [All 94 tests pass](checks_after_path_fix.json).
- [Reloaded-model inference](inference.json) matches all 345 saved local
  evaluation scores exactly, with identical flags.
- [Real HTTP versus CLI and local evaluation](http/http.json) matches all 345
  specimens; maximum score difference `1.11e-16`, identical flags. The check
  reverses target order and rejects malformed and oversized batches.
- [Demo verification](demo_service.json) checks all four public specimens and
  walkthroughs, the rejected incomplete file, assets and displayed evaluation
  counts. Its maximum score difference is zero.

The initial [test record](checks.json) preserves one failure. In
`tests/test_api.py`, the mock expected the temporary path through `/var` while
the application correctly resolved it through `/private/var`. The assertion now
uses `self.root.resolve()`. This is the only edit to an existing tracked file.
Training, preprocessing, application code, the lockfile and the input manifest
are unchanged. No commit or push was made.

Docker CLI is installed, but `docker info` found no running daemon. The serving
bundle was prepared and checked against the native local service using
`verify_container.py --url`; this is **not** evidence of a Docker build or
container run on this machine. Cloud deployment was not attempted. The already
committed presentation files were not regenerated.

## Use this clone

The demo was left running at [http://127.0.0.1:8765](http://127.0.0.1:8765).
To restart it later, run from the project root:

```sh
sh data/processed/setup/20260922_mac_clone/run_demo.sh
```

For a terminal that has uv, the virtual environment and this run's configuration:

```sh
source data/processed/setup/20260922_mac_clone/activate.sh
uv run --frozen uvicorn kidney_biopsy.api:app --host 127.0.0.1 --port 8765 --no-access-log
```

Use either launch method, not both simultaneously on the same port. The helper
contents are simple environment exports and the documented Uvicorn command.
Raw data, models, predictions, environment, caches, demo files and the container
bundle remain Git-ignored. New aggregate results and this audit remain visible
as untracked files for review.
