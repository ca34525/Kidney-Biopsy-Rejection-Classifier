# Windows and macOS setup

Run commands from this repository's root in PowerShell on Windows or Terminal
on macOS. Install `uv`, then use the project's locked Python 3.12 environment:

```sh
uv sync --frozen
```

Create a separate `.venv` on each computer. Git includes code, reports and the
presentation, but excludes raw data, fitted models, prepared examples and local
environments. Pulling the branch does not transfer those files.

The project's [uv cache keys](https://docs.astral.sh/uv/reference/settings/#cache-keys)
include package source and web assets, so installed wheels rebuild after those
files change. This prevents a cached wheel from serving a previous branch's UI.

### This Windows computer's build policy

During the September 27 check, Windows Application Control blocked uv's temporary
build interpreter (`os error 4551`). With a working project `.venv` already present,
the following built the package using that interpreter without changing Windows
security settings:

```sh
uv pip install --python .venv/Scripts/python.exe "setuptools>=77"
uv sync --frozen --no-build-isolation
```

The build dependency is declared in `pyproject.toml`; uv removes the extra installed
copy after syncing. The usual launch command works after this one-time build.
A completely fresh local install remains subject to that computer policy. Hosted
CI uses the ordinary isolated build on each operating system.

## Existing Windows checkout

This computer has the preserved `20260915_shared` model. Prepare matching public
examples once, then start the presentation and scoring app together:

```sh
uv run --frozen python scripts/prepare_demo.py --results-dir results/reproduction/20260915_shared --output-dir data/demo/20260927_windows
uv run --frozen python presentation/source/serve_demo.py --run-dir results/reproduction/20260915_shared --demo-dir data/demo/20260927_windows
```

The examples above were prepared during the September 27 check; skip preparation
when that directory already exists. Preparation refuses to overwrite it.

## Existing Mac checkout

The committed presentation configuration still selects the Mac's preserved
`20260922_mac_clone` model and `data/demo/20260922_ui_examples`. Start it with:

```sh
uv run --frozen python presentation/source/serve_demo.py
```

With the existing environment and no uv on PATH, use
`.venv/bin/python presentation/source/serve_demo.py` on macOS or
`.venv/Scripts/python.exe presentation/source/serve_demo.py` on Windows, adding
the Windows run/example options above.

On either system, open [the presentation](http://127.0.0.1:8766/presentation/engineering_demo.html)
or [the scoring app](http://127.0.0.1:8766/). Stop the server with Ctrl+C.
Use `--port 8767` if the default port is occupied. The application link follows
the running server's port.

The launcher verifies the selected model and matching examples before starting.
Both `--run-dir` and `--demo-dir` are required when overriding the configuration.
It reports missing files instead of silently switching runs or retraining.

The presentation's saved API example remains the dated Mac response. The live
application displays the selected run's model version, threshold and results.
The two preserved runs agree on the main error counts, but have small numeric
differences; they are not interchangeable model artifacts.

## Clean checkout on either system

Use a new run name in place of `my_run` throughout these commands. Completed
runs are preserved. The downloader checks existing inputs and fetches only
missing public files.

```sh
uv sync --frozen
uv run --frozen python experiments/rejection_public/download.py
uv run --frozen python scripts/verify_local_data.py
uv run --frozen python experiments/rejection_public/run.py --output-dir results/reproduction/my_run --model-dir data/processed/models/my_run
uv run --frozen python scripts/prepare_demo.py --results-dir results/reproduction/my_run --output-dir data/demo/my_run
uv run --frozen python presentation/source/serve_demo.py --run-dir results/reproduction/my_run --demo-dir data/demo/my_run
```

This reproduces the fixed training procedure locally. Keep its new run identity;
retraining on another operating system need not produce identical floating-point
scores or model-file hashes. The new run does not replace the dated slide results
or the saved presentation example.

## Verify

These checks need neither public data nor the research model:

```sh
uv run --frozen ruff check src scripts tests experiments
uv run --frozen ruff format --check src scripts tests experiments
uv run --frozen python scripts/check_project.py
uv run --frozen python presentation/source/check_demo.py --offline
```

With the Mac presentation server running, check its saved response using
`uv run --frozen python presentation/source/check_demo.py`. With the Windows
server running, use:

```sh
uv run --frozen python presentation/source/check_demo.py --run-dir results/reproduction/20260915_shared
```

For another run, substitute its path. Use `--url http://127.0.0.1:8767` when
testing another port. Live checks require the expected model identity and flags;
scores use absolute tolerance `1e-12`. Offline checks allow only LF/CRLF newline
conversion in embedded source text, while verifying the saved source hashes.
Substantive source changes require rebuilding the HTML.

GitHub Actions checks Windows, macOS and Linux with the locked environment and
an installed package. Tests build small synthetic models, exercise the launcher
in a path containing spaces, and check valid and invalid inputs. Linux also
builds and verifies the Docker image. Full research training stays outside CI.
See [verification](VERIFICATION.md) for the 345-specimen HTTP and fresh-install
checks, and [presentation rebuilding](../presentation/README.md#source-and-build-files)
for authoring dependencies. Node and slide-authoring tools are unnecessary to
run the existing demo.
