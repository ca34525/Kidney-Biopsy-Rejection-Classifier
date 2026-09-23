# Software verification

Run checks from the project root using Python 3.12 and uv. Use a new output
name for each check. Saved records establish behavior at their recorded revision;
a historical pass does not verify later edits.

## Fast checks

```powershell
uv sync --frozen
uv run --no-sync ruff check src scripts tests experiments
uv run --no-sync ruff format --check src scripts tests experiments
$checkName = Get-Date -Format 'yyyyMMdd-HHmmss'
uv run --no-sync python scripts/check_project.py --output "results/checks/$checkName/checks.json"
```

Ruff checks for basic Python mistakes, unused or undefined names, and import order.
Its formatter gives the source a consistent layout, with a target line length of
100 characters. The pinned development version and small rule list are in
`pyproject.toml`. The two commands above report problems without changing files.
To apply import fixes and formatting while editing, run:

```powershell
uv run --no-sync ruff check --fix src scripts tests experiments
uv run --no-sync ruff format src scripts tests experiments
```

Review the diff after applying fixes. The configuration excludes `results`,
`data`, build output, and caches, including when a preserved file is named
explicitly. Completed runs keep their original source snapshots. Three research
scripts allow imports after their local-path or plotting setup; this is the only
file-specific lint exception. Ruff is not a static type checker. Its
[configuration](https://docs.astral.sh/ruff/configuration/) and
[rule reference](https://docs.astral.sh/ruff/rules/) explain the selected checks.

The final command checks Python syntax, parses the project and lock TOML files,
checks the local package and its HTML/CSS/JavaScript assets, and runs the test suite.
Tests use small generated fixtures and require no public downloads or trained
research model. The JSON records source hashes, package versions, test counts,
failures, and elapsed time. Lint and formatting results appear separately in the
terminal and CI log so a failed check is easy to identify.

The [CI workflow](../.github/workflows/checks.yml) runs the same checks after
`uv sync --locked --no-editable` on Python 3.12. `--locked` fails if dependency
declarations disagree with the lockfile. The noneditable installation builds
and installs the package, so missing packaged web assets fail the check. Lint and
format checks run before tests. CI saves the small JSON evidence as an artifact.
The workflow then builds a container with a tiny synthetic CatBoost model and
checks readiness, predictions, displayed error counts, and invalid input over
HTTP. Both JSON check records are retained. Full research model training stays
outside CI. See the [container guide](CONTAINERS.md) for the same commands locally.

The workflow uses the documented interfaces for [checkout](https://github.com/actions/checkout),
[setup-uv](https://github.com/astral-sh/setup-uv), and
[upload-artifact](https://github.com/actions/upload-artifact), checked on
September 15, 2026. The workflow has a verified hosted pass, recorded below.
That pass covers its listed revision rather than every subsequent local edit.

## HTTP and fresh-install checks

The HTTP check starts its own local server, sends targets in reverse order,
compares all 345 validation specimens with CLI and saved scores at tolerance
1e-12, checks flags, and rejects malformed or oversized batches.

```powershell
$checkName = Get-Date -Format 'yyyyMMdd-HHmmss'
uv run --frozen python scripts/verify_http_service.py --output-dir "results/checks/$checkName/http" --case-dir "data/processed/application_checks/$checkName"
```

Use `--run-dir results/reproduction/20260922_mac_clone` for the laptop's run.
Otherwise the verifier uses the generic desktop default. The presentation has
its own [launcher and integration check](../presentation/README.md).

The fresh-install check physically copies selected source, raw data and the
configured model into a new ignored directory. It installs the locked package
noneditably, verifies hashes and packaged assets, runs tests, and compares two
public specimens through CLI/API. It needs network access for dependencies;
it does not redownload assay inputs or retrain models.

```powershell
$checkName = Get-Date -Format 'yyyyMMdd-HHmmss'
uv run --no-sync python scripts/verify_fresh_setup.py --run-dir results/reproduction/20260915_shared --check-dir "data/processed/setup_checks/$checkName" --output "results/checks/$checkName/fresh_setup.json"
```

Select the Mac run with the same `--run-dir` option when that is the available
model. Keep specimen inputs and outputs in the ignored case directories.
Container build and verification commands are in [Containers](CONTAINERS.md).

## Saved evidence

| Date and scope | Result and source |
| --- | --- |
| September 22: Mac setup | [94 tests](../results/checks/20260922_mac_clone/checks_after_path_fix.json), [345-specimen HTTP agreement](../results/checks/20260922_mac_clone/http/http.json), [model reload](../results/checks/20260922_mac_clone/inference.json), and [public examples](../results/checks/20260922_mac_clone/demo_service.json). The [setup record](../results/checks/20260922_mac_clone/README.md) separates reproduction differences from software checks. |
| September 21: source and presentation corrections | [Check record](../results/checks/20260921_source_review/README.md), including preservation of baseline and service artifacts. |
| September 17: local application | [94 tests, HTTP agreement, research container and artifact checks](../results/checks/20260917_coherence/README.md). |
| September 17: initial containers | [78 tests and research/synthetic image checks](../results/checks/20260917_ci_docker/README.md). |
| September 15: fresh installation | [55 tests and installed CLI/API agreement](../results/checks/20260915_application/fresh_setup_final.json); [browser behavior](../results/checks/20260915_application/browser.json). |
| September 15: audit and readability | [Audit findings and acceptance evidence](AUDIT.md), including the complete 27-fit reproduction and report comparisons. |
| September 15: shared-code extraction | [Fixed-procedure reproduction](../results/checks/20260915_shared/reproduction.json), [tests](../results/checks/20260915_shared/tests.json), and [reloaded-model agreement](../results/checks/20260915_shared/reproduced_inference.json). |

### Hosted CI: verified September 17, 2026

[Software checks #8](https://github.com/ca34525/Kidney-Biopsy-Rejection-Classifier/actions/runs/35270209322)
passed for PR #2 head `ce34d4c79442098308c89ca4ccb34542c4010216`:
installed-package tests, lint, formatting and a synthetic-container check.
This is evidence for that revision, not a cloud deployment or a pass for later edits.

### Desktop container checks: September 17, 2026

The [September 17 record](../results/checks/20260917_coherence/README.md) verifies
four public walkthroughs in a research container and all 345 HTTP/CLI/saved scores.
It also records restored line endings matching the original artifact manifests.
Later Mac checks are listed above; they did not run Docker on the Mac. No cloud
deployment has been performed.
