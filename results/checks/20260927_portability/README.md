# Windows and macOS portability check

September 27, 2026, on Windows x86-64 with Python 3.12.13 and the locked
dependencies. Research models, thresholds, raw inputs and completed runs were
preserved. No models were retrained during this check.

## Results

- [Hosted Software checks #41](https://github.com/ca34525/Kidney-Biopsy-Rejection-Classifier/actions/runs/36334477380)
  passed for commit `2e601ca99226a0905165ab9f57f62b5baa8ff9df` on **Windows,
  macOS and Linux**, including clean installed-package tests and offline
  presentation checks. The Linux Docker build and prediction check also passed.
- [Installed package](installed_checks_final.json): **105 tests passed**; packaged
  HTML, CSS and JavaScript match the working source. Ruff lint and formatting
  passed for `src`, `scripts`, `tests` and `experiments` (39 Python files).
- [Real HTTP and CLI](http_final/http.json): all **345 validation specimens** match
  the saved Windows run's scores and flags. Maximum score difference is
  `1.1102230246251565e-16`, below the `1e-12` tolerance. Reordered targets work;
  malformed and oversized batches fail.
- [Live presentation](live_presentation.json): the Windows run serves the
  engineering page, scoring application and speaking script; a complete public
  specimen scores correctly and removing IFNG returns 422 without a score.
- [Offline presentation](offline_presentation.json): 18 embedded references match
  their source text, allowing only LF/CRLF conversion; saved source hashes remain
  checked. The 14 slides and three browser stops retain their 1,200-second plan.
- Both local public inputs passed their manifest checks: 15,992,466 bytes total.

The Windows launcher uses `results/reproduction/20260915_shared` with seven public
examples prepared in `data/demo/20260927_windows`. The default configuration and
saved API snapshot still identify the Mac's `20260922_mac_clone` run. The Mac
model is absent on this computer, so this check does not claim to execute that
artifact here. Earlier Mac research evidence remains in its dated check directory.

## Problems found and fixed

1. The presentation launcher required Mac-only ignored files. It now accepts an
   explicit run and matching examples and checks them before opening a port.
2. The installed-package check caught an older cached wheel's HTML. uv cache keys
   now include package source and web assets. A rebuilt wheel passed all checks.
3. Mixed Python line endings caused a Windows formatting failure. Git now uses LF
   for active Python files and workflows, preserving the original bytes in research
   snapshots and presentation records. Embedded-source checks allow LF/CRLF changes
   but still reject changed calculations or broken hashes.
4. The presentation's exact JSON comparison could reject harmless cross-platform
   rounding. Scores and thresholds now use the existing `1e-12` tolerance, while
   model identities, flags and other response fields must match.

## Installation scope

The first clean-copy attempt was blocked by sandbox network access. After network
access was granted, Windows Application Control blocked the newly created uv build
interpreter (`os error 4551`). A build using the existing project interpreter and
the declared setuptools build dependency succeeded with `--no-build-isolation`.
Both the installed wheel and the normal editable environment were rebuilt.

The fresh-copy failure records are retained alongside the successful checks.
No Windows security settings were changed. A clean local installation is therefore
not claimed; the [setup guide](../../../docs/SETUP.md) records the working procedure.
The CI matrix performs ordinary clean installs on Windows, macOS and Linux and
runs the same tests plus the offline presentation check. The Linux job also
builds and verifies the synthetic Docker image. Hosted results are linked above.

## Commands

```sh
uv sync --locked --no-editable
uv run --no-sync python scripts/check_project.py --require-installed --output results/checks/20260927_portability/installed_checks_final.json
uv run --no-sync python scripts/verify_http_service.py --output-dir results/checks/20260927_portability/http_final --case-dir data/processed/application_checks/20260927_portability_final
uv run --frozen python presentation/source/serve_demo.py --run-dir results/reproduction/20260915_shared --demo-dir data/demo/20260927_windows
uv run --no-sync python presentation/source/check_demo.py --run-dir results/reproduction/20260915_shared --output results/checks/20260927_portability/live_presentation.json
uv run --no-sync python presentation/source/check_demo.py --offline --output results/checks/20260927_portability/offline_presentation.json
```

The first command encountered the local build policy described above; the
successful wheel build used `uv sync --frozen --no-editable --no-build-isolation`
after installing setuptools into the existing environment. Use new destinations
when repeating checks that refuse to overwrite evidence.
