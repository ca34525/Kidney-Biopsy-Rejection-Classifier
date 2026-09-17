# Figures for the interview presentation

These are new views of the preserved primary analysis, not new evaluation results.
The SVG files retain editable text; the PNG files are 2400 × 1350 pixels.

## Model errors

Use `01_model_errors.svg` for the main model comparison. The same 345 author
technical-validation specimens include 169 recorded rejection and 176 no-rejection
diagnoses. Each model retains its own discovery-selected threshold. CatBoost
missed 25 rejection cases and produced 8 false flags; logistic regression missed
33 with 8 false flags; IFNG missed 14 with 75 false flags. The constant baseline
appears as a note so it does not compress the comparison's scale. CatBoost's
practical advantage over logistic regression remains uncertain; the paired
miss-count interval includes no difference. See the original analysis for intervals.

## Score reliability

Use `02_score_reliability.svg` when explaining the score label, or in backup
material. Each point is one fixed score bin; the numbers along the bottom give
its specimen count. Bars are 95% Wilson intervals for the observed rejection
fraction. The dashed line shows agreement between mean score and observed fraction.
The highlighted 0.8–0.9 bin was chosen descriptively after inspection, not as a new
threshold or a formal subgroup claim. A Brier score combines discrimination and
calibration; it is not proof of reliable individual probabilities. No calibration
model was fitted on the validation specimens.

## Source and reproduction

Source: [preserved primary analysis](../../analysis/20260915_baseline/REPORT.md).
`manifest.json` records the source aggregate hashes, generating script, environment
lockfile, and output hashes. The script verifies aggregate files against their
existing analysis manifest before reading them. All displayed numbers come from
those files; no specimens, thresholds, or model parameters are changed.

Run from the project root, using a fresh output directory:

```powershell
uv run --frozen python scripts/prepare_presentation_figures.py --output-dir results/presentation/NEW_evidence
```
