# September 15 implementation audit

This dated review records consequential fixes and their acceptance evidence.
Use [Methodology review](METHODOLOGY_REVIEW.md) for the current analytical
assessment and [Verification](VERIFICATION.md) for commands and later checks.

## Findings and fixes

The review found no result-invalidating leakage, label, split or metric error in
the inspected workflow. It identified these software and reporting defects:

| Finding | Correction |
| --- | --- |
| Boolean and complex counts could be converted into usable numbers. | Reject them before conversion and test the count contract. |
| Repeated GEO fields could replace diagnoses or cohort assignments. | Reject duplicate fields and missing or duplicate specimen-accession rows. |
| Analysis duplicated label, hash and path rules; a path check allowed filesystem links. | Reuse shared helpers and record their hashes in new analysis manifests. |
| An existing empty subtype output directory failed too late. | Reject existing destinations before starting the run. |
| The viral report could repeat conclusions from another run. | Derive ranks, diagnoses and error counts from the supplied run. |
| Malformed optional example descriptions could break the example-list endpoint. | Validate the local example manifest while keeping uploads available. |
| Dense implementation and repeated history obscured the prediction path. | Expose named training, analysis, API and browser steps; separate setup from development history. |

The first pass preserved fitted models and thresholds. The readability pass
reran the fixed 27-fit procedure in a new directory, preserving prior runs.
Training and serving still share preprocessing and prediction; no extra framework
or application scoring path was introduced.

## Acceptance evidence

| Check | Dated record |
| --- | --- |
| 64 tests passed after the fixes | [Final checks](../results/checks/20260915_audit/final.json) |
| All 345 HTTP, CLI and saved scores agreed within 1e-12, with identical flags | [HTTP comparison](../results/checks/20260915_audit/http/http.json) |
| Fourteen aggregate CSVs and primary metrics JSON reproduced byte-for-byte | [Report comparison](../results/checks/20260915_audit/report_comparison.json) |
| Existing model and run artifacts remained intact | [Preserved runs](../results/checks/20260915_audit/preserved_runs.json) |
| All nine prediction tables, selected models, thresholds and assignments reproduced exactly after refactoring | [Full reproduction](../results/checks/20260915_readability/reproduction.json) |
| Valid, invalid, batch, stale-result and changed-model browser behavior passed | [Browser checks](../results/checks/20260915_readability/browser.json) |
| Eight aggregate tables, metrics JSON and six PNG charts reproduced byte-for-byte | [Analysis comparison](../results/checks/20260915_readability/analysis_comparison.json) |

These records cover their recorded revisions. They establish software consistency,
not independent clinical validation. File validation does not replace laboratory
QC, and the public data cannot verify patient or referring-center separation.
The later [full-study review](references/STUDY_AUDIT_20260919.md) also established
that the evaluated population includes native-kidney controls.
