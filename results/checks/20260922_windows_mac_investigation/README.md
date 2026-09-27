# Windows–Mac comparison with the original models

September 22, 2026. This is a bounded investigation, requested after the original
Windows artifacts became available. The user prioritized meaningful prediction
differences over tiny numerical changes and asked not to spend heavily on it.

**Every saved specimen-level label and flag compared agrees between Windows and
Mac.** The main application's results reproduce at the level that affects its
reported errors: CatBoost misses the same 25 rejection specimens and falsely
flags the same 8 no-rejection specimens. Logistic regression misses the same
33 and falsely flags the same 8. This directly checks individual predictions;
it is stronger evidence than the previous comparison of aggregate counts.

The Windows original was read only. No original model was adopted by this
project. Existing research runs, production code, presentation sources, and the
frozen application model were not changed. The only new fit was one diagnostic
repeat of the existing depth-6 stability candidate; it was kept in memory.

## What was compared

| Evidence | Result |
| --- | --- |
| Both physical public source files | SHA-256 hashes match between Windows and Mac |
| Current training, preprocessing and source-reading code; lockfile and project dependencies | Same text after newline normalization |
| Functions/classes in the Windows readability-run snapshots versus Mac primary-run snapshots | Identical Python syntax trees for training, preprocessing and source reading; formatting/import ordering differ |
| All 18 primary screening/validation prediction tables | Same specimen identities, recorded labels and flags; 5,472 model/specimen rows |
| All 40 stability screening/assessment prediction tables | Same specimen/model identities, labels and flags; 29,400 rows across overlapping repetitions |
| Both subtype prediction tables | Same specimen identities, diagnosis predictions and flags; 608 specimens |
| Nine original primary models loaded on Mac | Same validation flags as their saved Windows predictions; score differences no larger than 2.11e-15 |
| Three selected primary CatBoost models | Same tree decisions in Windows and Mac models |
| Forty saved stability CatBoost candidates | Same tree decisions in 39; one differs late in training |

The row totals count repeated predictions, not independent patients. Comparisons
align specimens by ID (and model where applicable), check unique keys, require
matching columns, and reject missing values. No tolerance is used for flags or
labels. Numeric differences are recorded separately without relabeling a strict
numerical mismatch as an exact reproduction.

## Where the notable CatBoost difference occurs

“Stability” is the discovery-only follow-up that repeats the model comparison
with 20 fixed specimen splits. Each repetition tests three logistic settings and
two CatBoost depths. A candidate is simply one of these fitted alternatives.

In repetition 6, the depth-6 CatBoost models use the same fitted parameters,
including seed and thread count, but their first different tree decisions occur
at **tree 294 of 300**. Six trees have different decisions: 294–296 and 298–300.
The model was not selected in that repetition. Across all 43 inspected CatBoost
pairs, the fitted parameter dictionaries agree.

One unchanged Mac refit of this candidate gives **exactly the earlier Mac
screening scores**. Loading the Windows candidate on Mac gives **exactly its
saved Windows screening scores**. The Windows-versus-Mac candidate scores differ
by up to 0.02148 on those screening rows, but their saved screening flags agree.
The saved specimen assignments also agree.

This establishes that the difference is in the fitted model produced during
training, rather than in scoring the saved Windows model on Mac. Platform-specific
numerical behavior during training is a plausible explanation, especially given
the late divergence and matching code/settings. **The precise low-level cause
was not isolated**: this investigation did not execute the original Windows
training runtime or measure its intermediate floating-point calculations.

## ExtraTrees and the stopping point

ExtraTrees is another ensemble of decision trees, with random choices of features
and split thresholds. This experiment used 400 trees. It was screened as an
alternative and was not selected for any of the three primary targets.

The earlier aggregate audit showed one additional false flag in its Mac
antibody-mediated screening result (12 versus 11). The training script retains
the selected models, logistic regression and IFNG; it does not retain this
unselected ExtraTrees model or its specimen-level scores. Thus the supplied
primary artifacts do not support the same direct model inspection for ExtraTrees.
Its exact cause remains unresolved. The aggregate discrepancy is preserved in
the [earlier audit](../20260922_mac_clone/README.md#differences-and-limits).

The primary model choices and meaningful reported performance reproduce. A claim
that *every fitted candidate and every number is identical across platforms*
would be too strong. The demonstrated result is that the main prediction flags,
the saved subtype predictions, and all saved stability flags agree. Further
compiler/library-level investigation is deferred at the user's request.

## Evidence and repeat commands

- [Prediction comparisons](prediction_comparison.json): all saved tables, input hashes and source checks.
- [Model inspection](model_inspection.json): original-model scoring, tree decisions, source-function checks and original file hashes.
- [Single diagnostic refit](repeat_six.json): exact Mac repeat and original Windows-model scoring checks.

The model inspection records and rechecks hashes for the 58 Windows model and
prediction files it opens. All remain unchanged. Other Windows paths are only
read. These audit scripts explicitly refer to the supplied sibling folder; the
normal project workflow retains no dependency on it.

Run from this project root in its own environment:

```sh
uv run --frozen python results/checks/20260922_windows_mac_investigation/compare_predictions.py
uv run --frozen python results/checks/20260922_windows_mac_investigation/inspect_models.py
PYTHONPATH=. uv run --frozen python results/checks/20260922_windows_mac_investigation/repeat_six.py
```

These commands rewrite only this investigation's JSON evidence, never historical
research runs or the Windows original. The local commands used `.uv-cache/bin/uv`.
An initial diagnostic-refit attempt stopped before fitting because it redundantly
renamed a metadata column already supplied by the parser; removing that redundant
rename allowed the unchanged experiment to run.
