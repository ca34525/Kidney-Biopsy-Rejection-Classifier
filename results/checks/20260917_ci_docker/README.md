# CI and container verification

Verified September 17, 2026, on branch `codex/ci-and-container`.

The project now checks Python mistakes and formatting, then tests the installed
application and builds a running container in its GitHub Actions workflow. The
research image was built and exercised locally with Docker Desktop's Linux engine.

| Check | Result | Record |
| --- | --- | --- |
| Existing tests before changes | 64 passed | [Baseline](before_quality.json) |
| Final installed-package checks | 78 passed | [Complete checks](complete_checks.json) |
| Ruff lint and formatting | Passed on 31 active Python files | Commands below |
| Real research image | Four valid specimens matched local scores exactly; one invalid example rejected | [Research container](research_container.json) |
| Synthetic CatBoost image used by CI | Valid score matched exactly; invalid example rejected | [Synthetic container](synthetic_container.json) |
| Hosted GitHub Actions | Not run for this branch during this work | Requires pushing the branch |
| AWS deployment | Prepared procedure and configuration; no cloud resources created | [AWS guide](../../../docs/AWS_DEPLOYMENT.md) |

Both container checks verified readiness, the page and static assets, model and
schema identity, threshold, prepared CSVs, displayed evaluation counts, scores,
and flags. They ran as user `10001:10001` with a read-only filesystem and removed
their temporary containers. Research score tolerance was `1e-12`; the measured
maximum difference was zero. This checks software packaging and scoring agreement,
not classifier accuracy on new specimens.

The research image is available locally as `kidney-biopsy:demo`. Its Docker-reported
size was 277,405,254 bytes. The complete research check took 4.332 seconds, including
container startup and removal. The JSON records the image ID and serving-bundle
hash. The synthetic image is labeled `kidney-biopsy:ci`; use the research image
for an interview demonstration or deployment.

The original completed research runs, fitted models, and source snapshots were
preserved. Existing Python edits consist of formatting, import cleanup, a small
lambda-to-function rewrite, and recording the Ruff version in software checks.
No research model was retrained. The new tests cover serving-bundle integrity,
model/example mismatches, unsafe paths, missing artifacts, changed scores, and
missing or changed displayed evaluation counts.

Commands used for the final quality checks:

```powershell
uv sync --locked --no-editable
uv run --no-sync ruff check src scripts tests experiments
uv run --no-sync ruff format --check src scripts tests experiments
uv run --no-sync python scripts/check_project.py --require-installed --output results/checks/20260917_ci_docker/complete_checks.json
```

Use a new output path when repeating checks. Container commands and the explanation
of each file are in the [container guide](../../../docs/CONTAINERS.md).

Codex assisted with these changes, tests, documentation, and independent review.
The user set the scope and required understandable implementation. Review found
and fixed a check that could miss absent evaluation counts and a cleanup path
that could leave a container after a failed start. Docker Desktop needed a local
stale-socket recovery before it could start; the old socket directories were
preserved, and existing image disks and settings were retained.
