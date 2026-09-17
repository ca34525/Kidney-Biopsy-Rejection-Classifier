# Build and check the container

The container runs the same prediction service as the local Python command. It
contains the selected model, its verified metadata, the observed error counts,
and the prepared public examples. It starts without training or downloading data.

Run these commands from the project root. Use Python 3.12, uv, and a running
Docker engine in Linux container mode. On Windows, Docker Desktop provides that
engine. `docker version` must report both a client and a server.

## Prepare, build, verify

In this populated project, the selected model and examples already exist:

```powershell
uv sync --frozen
uv run --no-sync python scripts/prepare_container.py
docker build --platform linux/amd64 --tag kidney-biopsy:demo .
$checkName = Get-Date -Format 'yyyyMMdd-HHmmss'
uv run --no-sync python scripts/verify_container.py --image kidney-biopsy:demo --output "results/checks/$checkName/container.json"
```

The preparation command creates `build/container` and refuses to overwrite it.
Reuse that folder while the selected model and examples are unchanged. To select
a different completed run, first move the existing bundle to another directory
under ignored `build/`, then prepare its replacement:

```powershell
$bundleBackup = 'build/container-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
Move-Item -LiteralPath build/container -Destination $bundleBackup
uv run --no-sync python scripts/prepare_container.py --results-dir "results/reproduction/$runName" --demo-dir "data/demo/$runName"
```

Here `$runName` identifies the run and examples produced by the README's
[clean-checkout commands](../README.md#reproduce-from-a-clean-checkout). A fresh
checkout must produce its own model before preparing the research image.

The check starts a temporary container bound to localhost on an available port,
then removes that container. It verifies:

- The configured user is not root, and the service works with a read-only filesystem.
- `/health` reports that the model loaded; the image's own readiness command passes.
- The page, CSS, JavaScript, public example listing, and example files are available.
- Model identity, schema, threshold, and displayed error counts match the bundle.
- All valid examples match local scores within `1e-12`, with identical flags and metadata.
- The invalid example returns HTTP 422 and a structured explanation.

The JSON record contains image ID/size, model version, aggregate checks, and elapsed
time. It contains no uploaded specimens. Failure returns a nonzero exit code.

## Open the demonstration

```powershell
docker run --rm --name kidney-biopsy-demo --read-only --cap-drop ALL --security-opt no-new-privileges --publish 127.0.0.1:8000:8000 kidney-biopsy:demo
```

Open [the container demonstration](http://127.0.0.1:8000). Press Ctrl+C to stop it.
`--rm` removes this container after it stops; the image remains available.

If Docker Desktop is installed outside PATH, add its `resources/bin` folder to
this terminal's PATH or use its full executable path. The checker also accepts
`--docker path/to/docker.exe`. Keep machine-specific paths out of project files.

## What each file does

| File | Purpose |
| --- | --- |
| `scripts/prepare_container.py` | Verify selected source artifacts and copy only the serving files |
| `build/container/bundle.json` | Record selected run, example directory, model version, and copied file hashes |
| `.dockerignore` | Admit only application source, the lockfile, launcher, and prepared bundles to Docker |
| `Dockerfile` | Install locked dependencies, copy the serving bundle, and configure the unprivileged service |
| `scripts/serve_container.py` | Read the bundled paths and start one API process on port 8000 |
| `scripts/verify_container.py` | Compare the running service with the verified local bundle |

The Dockerfile uses Python 3.12 and a fixed uv release. `uv sync --locked --no-dev
--no-editable` checks lockfile consistency and installs the application without
development tools. The Python base tag receives maintenance updates; identical
source is therefore not a promise of identical image bytes. The verification
record identifies the actual image that was checked.

The bundle keeps the original manifests and paths. Those manifests also describe
research files that are not needed for serving; only the files listed in
`bundle.json` are copied. Data downloads, other fitted models, prior analyses,
local environments, and credentials stay outside the build context. Original
research files remain unchanged.

This follows the documented [uv Docker integration](https://docs.astral.sh/uv/guides/integration/docker/)
and [Docker build guidance](https://docs.docker.com/build/building/best-practices/),
checked September 17, 2026.

## What CI demonstrates

Every push and pull request runs one workflow:

```text
install locked environment → lint → formatting → tests → build image → check running container
```

CI creates a tiny model labeled `synthetic-ci-only` with generated counts. It
uses the same bundler, Dockerfile, launcher, and HTTP check as the real image.
This makes packaging failures detectable from a clean checkout without public
data downloads or a full research training run. These synthetic results are
software fixtures and provide no evidence of classifier performance.

CI builds and tests its image; it does not publish it or deploy it to an account.
For the interview deployment, use the real bundle and follow the
[AWS guide](AWS_DEPLOYMENT.md). That guide supplies the remaining account setup,
image upload, HTTPS deployment, verification, and cleanup steps.
