"""Repeat the CatBoost/logistic choice using discovery data only.

Run from the project root with ``uv run python -m experiments.rejection_stability.run``.
The frozen service and original author-validation results are not changed.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
import time
import warnings
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from kidney_biopsy import (
    AssaySchema,
    map_diagnoses,
    normalize_counts,
    predict_scores,
    read_geo_matrix,
    read_rcc_archive,
)
from scripts.verify_local_data import local_path, records, sha256, verify

ROOT = Path(__file__).resolve().parents[2]
DISCOVERY = "Discovery cohort sample"
VALIDATION = "Validation cohort sample"
PARTS = ("fit", "screen", "assessment")
FAMILIES = ("logistic", "catboost")
SEEDS = tuple(range(20260917, 20260937))
RELOAD_TOLERANCE = 1e-12


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def configuration() -> dict:
    return {
        "procedure": "Discovery-only model-selection stability follow-up; predefined 20 repetitions.",
        "target": "Any recorded rejection versus no rejection",
        "seeds": list(SEEDS),
        "split_sizes": {"fit": 630, "screen": 210, "assessment": 210},
        "split_method": (
            "train_test_split holds out 210 assessment specimens, then 210 screening specimens; "
            "both stages stratify by the four original diagnoses and use the repetition seed."
        ),
        "normalization": (
            "Shared specimen-only log2(raw count + 1) minus the mean of the 12 "
            "log2(housekeeping count + 1) values. All 758 non-housekeeping assay targets."
        ),
        "models": {
            "logistic_C0.01": {"family": "logistic", "C": 0.01},
            "logistic_C0.1": {"family": "logistic", "C": 0.1},
            "logistic_C1": {"family": "logistic", "C": 1.0},
            "catboost_depth4": {"family": "catboost", "depth": 4},
            "catboost_depth6": {"family": "catboost", "depth": 6},
        },
        "logistic_settings": {
            "penalty": "L2",
            "solver": "lbfgs",
            "max_iter": 2000,
            "scaling": "StandardScaler fitted on fit specimens only",
        },
        "catboost_settings": {
            "iterations": 300,
            "learning_rate": 0.04,
            "random_seed": 2026,
            "loss_function": "Logloss",
            "thread_count": 3,
        },
        "threshold_rule": "Highest screening score retaining at least 90% of screening rejection cases; score >= threshold.",
        "selection_rule": (
            "Within each family, maximum screening specificity, then ROC-AUC. "
            "Exact ties choose stronger logistic regularization or shallower CatBoost. "
            "Across the two winners, the same specificity/AUC rule applies; exact ties choose logistic. "
            "The fitted models and associated thresholds are retained without refitting."
        ),
        "assessment": (
            "Assess both family winners on the same held-out 210 discovery specimens. "
            "The chosen-family result uses that already frozen winner; assessment never changes selection."
        ),
        "summary": (
            "Selection counts; median, 10th/90th percentiles and range of per-repeat results; "
            "paired CatBoost-minus-logistic error/metric differences. Repeated specimens "
            "are not pooled as independent observations; quantiles are not confidence intervals."
        ),
        "scope": (
            "Source archive is parsed and validated in full, then only discovery rows are normalized, "
            "fitted and scored. The author-validation cohort is not evaluated. Existing results "
            "have been seen, so this is follow-up analysis. It evaluates a 630-fit-row procedure, "
            "not accuracy of the frozen 787-fit-row service model."
        ),
        "model_version": "20260917_stability:v1",
        "reload_tolerance": RELOAD_TOLERANCE,
    }


def discovery_data(metadata: pd.DataFrame, raw_counts: pd.DataFrame):
    if not metadata.index.is_unique or not raw_counts.index.is_unique:
        raise ValueError("Source specimen IDs must be unique.")
    if set(metadata.index) != set(raw_counts.index):
        raise ValueError("Raw counts and metadata must contain the same specimens.")
    if metadata.cohort.value_counts(dropna=False).to_dict() != {DISCOVERY: 1050, VALIDATION: 345}:
        raise ValueError("Expected the original 1,050 discovery and 345 validation specimens.")
    discovery = metadata.loc[metadata.cohort.eq(DISCOVERY)].copy()
    labels = map_diagnoses(discovery.histology_diagnosis)
    features = normalize_counts(raw_counts.loc[discovery.index])
    if features.shape != (1050, 758):
        raise ValueError("Expected 1,050 discovery specimens and 758 assay features.")
    if features.duplicated(keep=False).any():
        raise ValueError("Duplicate discovery profiles require a grouped split before fitting.")
    return discovery, features, labels


def validate_parts(parts: dict, metadata: pd.DataFrame) -> None:
    if set(parts) != set(PARTS):
        raise ValueError("Split requires fit, screen and assessment partitions.")
    if not metadata.index.is_unique or not metadata.cohort.eq(DISCOVERY).all():
        raise ValueError("Only unique discovery specimens may enter this procedure.")
    combined = [sample for part in PARTS for sample in parts[part]]
    if len(set(combined)) != len(combined) or set(combined) != set(metadata.index):
        raise ValueError("Partitions must be disjoint and cover discovery exactly once.")
    if [len(parts[part]) for part in PARTS] != [630, 210, 210]:
        raise ValueError("Expected 630 fit, 210 screening and 210 assessment specimens.")
    diagnoses = set(metadata.histology_diagnosis)
    map_diagnoses(metadata.histology_diagnosis)
    for part in PARTS:
        if set(metadata.loc[parts[part], "histology_diagnosis"]) != diagnoses:
            raise ValueError("Every partition must retain all original diagnoses.")


def split_discovery(metadata: pd.DataFrame, seed: int) -> dict:
    if len(metadata) != 1050 or not metadata.cohort.eq(DISCOVERY).all():
        raise ValueError("Split input must be exactly the 1,050 discovery specimens.")
    development, assessment = train_test_split(
        metadata.index.to_numpy(),
        test_size=210,
        stratify=metadata.histology_diagnosis.to_numpy(),
        random_state=seed,
    )
    fit, screen = train_test_split(
        development,
        test_size=210,
        stratify=metadata.loc[development, "histology_diagnosis"].to_numpy(),
        random_state=seed,
    )
    parts = {"fit": fit, "screen": screen, "assessment": assessment}
    validate_parts(parts, metadata)
    return parts


def make_candidates(config: dict) -> dict:
    candidates = {}
    for name, settings in config["models"].items():
        if settings["family"] == "logistic":
            candidates[name] = make_pipeline(
                StandardScaler(),
                LogisticRegression(C=settings["C"], max_iter=2000),
            )
        else:
            candidates[name] = CatBoostClassifier(
                depth=settings["depth"],
                **config["catboost_settings"],
                verbose=False,
                allow_writing_files=False,
            )
    return candidates


def screen_result(labels, scores) -> dict:
    labels, scores = np.asarray(labels), np.asarray(scores, dtype=float)
    if (
        labels.ndim != 1
        or scores.shape != labels.shape
        or set(labels) != {0, 1}
        or not np.isfinite(scores).all()
        or (scores < 0).any()
        or (scores > 1).any()
    ):
        raise ValueError("Screening needs both binary classes and finite scores in [0, 1].")
    # Same threshold rule as the original experiment; equality counts as a flag.
    positive_scores = scores[labels == 1]
    threshold = max(
        cutoff for cutoff in np.unique(scores) if np.mean(positive_scores >= cutoff) >= 0.9
    )
    return summarize_scores(labels, scores, threshold)


def summarize_scores(labels, scores, threshold) -> dict:
    labels, scores = np.asarray(labels), np.asarray(scores)
    tn, fp, fn, tp = confusion_matrix(labels, scores >= threshold, labels=[0, 1]).ravel()
    return {
        "n": int(len(labels)),
        "positives": int(labels.sum()),
        "threshold": float(threshold),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "sensitivity": float(tp / (tp + fn)),
        "specificity": float(tn / (tn + fp)),
        "ppv": float(tp / (tp + fp)) if tp + fp else None,
        "npv": float(tn / (tn + fn)) if tn + fn else None,
        "roc_auc": float(roc_auc_score(labels, scores)),
        "average_precision": float(average_precision_score(labels, scores)),
    }


def select_candidate(rows: list[dict]) -> dict:
    """Rank screening results only; exact ties resolve to the simpler option."""
    if not rows or any(row["sensitivity"] < 0.9 for row in rows):
        raise ValueError("Selection requires eligible screening results.")
    return max(
        rows,
        key=lambda row: (
            row["specificity"],
            row["roc_auc"],
            row["family"] == "logistic",
            -row["complexity"],
        ),
    )


def fit_and_screen(features, labels, parts, config, repeat_dir):
    """Only fit and screen rows are reachable from this fitting function."""
    models, rows, predictions = make_candidates(config), [], []
    for name, model in models.items():
        started = time.perf_counter()
        settings = config["models"][name]
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            model.fit(features.loc[parts["fit"]], labels.loc[parts["fit"]])
        scores = predict_scores(model, features.loc[parts["screen"]])
        row = {
            "model": name,
            "family": settings["family"],
            "complexity": settings.get("C", settings.get("depth")),
            **screen_result(labels.loc[parts["screen"]], scores),
            "fit_seconds": time.perf_counter() - started,
        }
        rows.append(row)
        artifact = repeat_dir / f"{name}.joblib"
        joblib.dump(model, artifact)
        reloaded = joblib.load(artifact)
        reload_scores = predict_scores(reloaded, features.loc[parts["screen"]])
        np.testing.assert_allclose(scores, reload_scores, rtol=0, atol=RELOAD_TOLERANCE)
        row["reload_max_abs_difference"] = float(np.max(np.abs(scores - reload_scores)))
        predictions.append(
            pd.DataFrame(
                {
                    "sample": parts["screen"],
                    "model": name,
                    "recorded_rejection": labels.loc[parts["screen"]].to_numpy(),
                    "score": scores,
                    "flag": scores >= row["threshold"],
                }
            )
        )
    pd.concat(predictions, ignore_index=True).to_csv(
        repeat_dir / "screen_predictions.csv", index=False
    )
    return models, rows


def freeze_and_assess(models, screen_rows, features, labels, parts, repeat_dir, model_version):
    winners = {
        family: select_candidate([row for row in screen_rows if row["family"] == family])
        for family in FAMILIES
    }
    selected = select_candidate(list(winners.values()))
    frozen = {
        "model_version": model_version,
        "selected_family": selected["family"],
        "selected_model": selected["model"],
        "families": winners,
        "schema": AssaySchema(features=tuple(features.columns)).to_dict(),
    }
    # Persist the decision before making any assessment predictions.
    write_json(repeat_dir / "frozen.json", frozen)
    rows, predictions = [], []
    for family, winner in winners.items():
        model = models[winner["model"]]
        scores = predict_scores(model, features.loc[parts["assessment"]])
        rows.append(
            {
                "family": family,
                "model": winner["model"],
                "selected": family == selected["family"],
                **summarize_scores(labels.loc[parts["assessment"]], scores, winner["threshold"]),
            }
        )
        predictions.append(
            pd.DataFrame(
                {
                    "sample": parts["assessment"],
                    "family": family,
                    "model": winner["model"],
                    "recorded_rejection": labels.loc[parts["assessment"]].to_numpy(),
                    "score": scores,
                    "threshold": winner["threshold"],
                    "flag": scores >= winner["threshold"],
                }
            )
        )
    pd.concat(predictions, ignore_index=True).to_csv(
        repeat_dir / "assessment_predictions.csv", index=False
    )
    return rows, {
        "selected_family": selected["family"],
        "selected_model": selected["model"],
        "logistic_model": winners["logistic"]["model"],
        "catboost_model": winners["catboost"]["model"],
        "screen_false_flags_tied": winners["logistic"]["fp"] == winners["catboost"]["fp"],
        "screen_false_flags_catboost_minus_logistic": winners["catboost"]["fp"]
        - winners["logistic"]["fp"],
    }


def distribution(values) -> dict:
    values = np.asarray(values, dtype=float)
    return {
        "median": float(np.median(values)),
        "p10": float(np.quantile(values, 0.1)),
        "p90": float(np.quantile(values, 0.9)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def summarize(assessment: pd.DataFrame, selections: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    metrics = ("fn", "fp", "sensitivity", "specificity", "roc_auc", "threshold")
    family_summary = {}
    for family in [*FAMILIES, "selected"]:
        frame = (
            assessment.loc[assessment.selected]
            if family == "selected"
            else assessment.loc[assessment.family.eq(family)]
        )
        family_summary[family] = {metric: distribution(frame[metric]) for metric in metrics}
        family_summary[family]["assessment_sensitivity_at_least_90_count"] = int(
            frame.sensitivity.ge(0.9).sum()
        )
    left = assessment.loc[assessment.family.eq("catboost")].set_index("repeat")
    right = assessment.loc[assessment.family.eq("logistic")].set_index("repeat")
    deltas = (
        left[["fn", "fp", "sensitivity", "specificity", "roc_auc"]]
        - right[["fn", "fp", "sensitivity", "specificity", "roc_auc"]]
    )
    deltas.columns = [f"{column}_catboost_minus_logistic" for column in deltas.columns]
    result = {
        "repetitions": len(selections),
        "assessment_n_each": 210,
        "assessment_rejection_n": distribution(assessment.positives),
        "selection_counts": selections.selected_family.value_counts().to_dict(),
        "selected_candidate_counts": selections.selected_model.value_counts().to_dict(),
        "within_family_choice_counts": {
            family: selections[f"{family}_model"].value_counts().to_dict() for family in FAMILIES
        },
        "screen_false_flags_tied_count": int(selections.screen_false_flags_tied.sum()),
        "screen_false_flag_difference": distribution(
            selections.screen_false_flags_catboost_minus_logistic
        ),
        "assessment": family_summary,
        "paired_catboost_minus_logistic": {
            column: distribution(deltas[column]) for column in deltas
        },
        "assessment_error_comparisons": {
            metric: {
                "catboost_fewer": int(deltas[f"{metric}_catboost_minus_logistic"].lt(0).sum()),
                "tied": int(deltas[f"{metric}_catboost_minus_logistic"].eq(0).sum()),
                "logistic_fewer": int(deltas[f"{metric}_catboost_minus_logistic"].gt(0).sum()),
            }
            for metric in ("fn", "fp")
        },
        "interpretation": "Repeated partitions overlap; quantiles describe split variability, not independent confidence intervals.",
    }
    return result, deltas.reset_index()


def make_figure(deltas, summary, output_dir):
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".uv-cache/matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.size": 17,
            "svg.fonttype": "none",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    figure, axes = plt.subplots(1, 2, figsize=(13.33, 7.5))
    figure.subplots_adjust(top=0.69, bottom=0.29, left=0.07, right=0.96, wspace=0.28)
    figure.text(
        0.06, 0.91, "Does the model choice depend on the split?", fontsize=26, weight="bold"
    )
    chosen = summary["selection_counts"]
    figure.text(
        0.06,
        0.83,
        f"Screening selected CatBoost {chosen.get('catboost', 0)}/20 times; logistic {chosen.get('logistic', 0)}/20.",
        fontsize=20,
    )
    figure.text(
        0.06,
        0.76,
        "Each point compares the two selected models on the same 210 held-out discovery specimens.",
        fontsize=15,
    )
    for axis, metric, title in zip(
        axes, ("fn", "fp"), ("Missed rejection", "False rejection flags")
    ):
        values = deltas[f"{metric}_catboost_minus_logistic"].to_numpy()
        # Stack ties so every one of the 20 repeats remains visible.
        heights = np.zeros(len(values))
        for value in np.unique(values):
            positions = np.flatnonzero(values == value)
            heights[positions] = np.arange(len(positions)) - (len(positions) - 1) / 2
        axis.axvline(0, color="#777777", linewidth=1.5, linestyle="--")
        axis.scatter(values, heights, s=100, color="#137c89", edgecolor="white", linewidth=1)
        axis.set_title(title, fontsize=21, pad=18)
        span = max(3, int(np.max(np.abs(values))) + 2)
        axis.set_xlim(-span, span)
        axis.set_ylim(-3.5, 3.5)
        axis.set_yticks([])
        axis.spines[["left", "bottom"]].set_visible(False)
        axis.set_xlabel("CatBoost errors minus logistic errors", fontsize=15, labelpad=14)
        axis.text(0, -0.36, "Fewer with CatBoost", transform=axis.transAxes, fontsize=14, ha="left")
        axis.text(
            1, -0.36, "Fewer with logistic", transform=axis.transAxes, fontsize=14, ha="right"
        )
    figure.text(
        0.06,
        0.08,
        "20 overlapping discovery splits; 630 fit / 210 screen / 210 assessment. These are not independent trials.",
        fontsize=14,
    )
    figure.text(
        0.06,
        0.04,
        "Follow-up analysis • thresholds chosen on screening only • author-validation results and service unchanged",
        fontsize=13,
        color="#555555",
    )
    figure.savefig(output_dir / "model_choice_stability.png", dpi=180)
    figure.savefig(output_dir / "model_choice_stability.svg")
    plt.close(figure)


def format_distribution(item, percentage=False):
    factor = 100 if percentage else 1
    suffix = "%" if percentage else ""
    return f"{item['median'] * factor:.1f}{suffix} ({item['p10'] * factor:.1f}–{item['p90'] * factor:.1f}{suffix})"


def write_report(summary, config, output_dir, artifacts_dir, elapsed):
    counts = summary["selection_counts"]
    table = []
    for family, label in (
        ("logistic", "Logistic"),
        ("catboost", "CatBoost"),
        ("selected", "Screening choice"),
    ):
        row = summary["assessment"][family]
        table.append(
            f"| {label} | {format_distribution(row['fn'])} | {format_distribution(row['fp'])} | {format_distribution(row['sensitivity'], True)} | {format_distribution(row['specificity'], True)} | {row['assessment_sensitivity_at_least_90_count']}/20 |"
        )
    report = f"""# Does the model choice depend on the development split?

This discovery-only follow-up selected CatBoost in **{counts.get("catboost", 0)} of 20** repetitions and logistic regression in **{counts.get("logistic", 0)} of 20**. The two family winners had identical screening false-flag counts in **{summary["screen_false_flags_tied_count"]} of 20** repetitions; ROC-AUC broke those operating-point ties. The original model choice therefore should be explained with its split sensitivity, not as an established universal advantage of one algorithm.

![Model-choice stability](model_choice_stability.png)

## What changed between repetitions

Each repetition uses the same 1,050 discovery specimens with a new fixed diagnosis-stratified assignment: **630 fit / 210 screen / 210 assessment**. Screening chooses among three full-panel logistic regularization strengths (C = 0.01, 0.1, 1) and two CatBoost depths (4, 6; 300 trees). Both families use all 758 assay predictors. The shared preprocessing normalizes each specimen with its 12 housekeeping targets; logistic scaling learns only from its fit partition.

For each candidate, the threshold is the highest screening score retaining at least 90% of recorded rejection cases. Within a family and between family winners, selection maximizes screening specificity, then ROC-AUC. Exact ties favor stronger regularization, shallower trees, and finally logistic regression. Each selected fitted model stays paired with its screening threshold; there is no refit. Choices are saved before assessment predictions. Every repetition uses the same partitions for both families.

The design, candidate list and all 20 seeds were saved before fitting. We did not expand the experiment in response to results. The source archive is parsed and checked in full, then only discovery rows enter normalization, fitting or scoring. The 345 author-validation specimens are not evaluated in this follow-up.

## Errors on held-out discovery specimens

Each assessment has 210 specimens: {int(summary["assessment_rejection_n"]["min"])}–{int(summary["assessment_rejection_n"]["max"])} with rejection and {210 - int(summary["assessment_rejection_n"]["max"])}–{210 - int(summary["assessment_rejection_n"]["min"])} without. Entries below show the median across repetitions, with the 10th–90th percentile range in parentheses. Fractional error counts summarize repetitions; an individual repetition always has integer counts.

| Procedure | Missed rejection | False flags | Sensitivity | Specificity | Reached 90% sensitivity on assessment |
| --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(table)}

The screening sensitivity target is an experiment setting; it is not a guarantee for unseen specimens. The “Screening choice” row evaluates the model family chosen before that repetition's assessment was scored.

## Paired comparison

Subtracting logistic errors from CatBoost errors within each repeat holds assessment specimens fixed:

- Missed-rejection difference: **{format_distribution(summary["paired_catboost_minus_logistic"]["fn_catboost_minus_logistic"])}**.
- False-flag difference: **{format_distribution(summary["paired_catboost_minus_logistic"]["fp_catboost_minus_logistic"])}**.
- CatBoost misses fewer rejection cases in {summary["assessment_error_comparisons"]["fn"]["catboost_fewer"]}/20 repeats, ties in {summary["assessment_error_comparisons"]["fn"]["tied"]}/20, and logistic misses fewer in {summary["assessment_error_comparisons"]["fn"]["logistic_fewer"]}/20.
- CatBoost makes fewer false flags in {summary["assessment_error_comparisons"]["fp"]["catboost_fewer"]}/20 repeats, ties in {summary["assessment_error_comparisons"]["fp"]["tied"]}/20, and logistic makes fewer in {summary["assessment_error_comparisons"]["fp"]["logistic_fewer"]}/20.

The full threshold distributions, candidate choices, metric ranges and paired ROC-AUC differences are in [summary.json](summary.json). Threshold variation is descriptive: different fits can have different score scales, and these thresholds should not be transferred between fitted models.

## What this establishes

This tests the model-selection procedure with 630 fit specimens, fewer than the original frozen model's 787. It does not re-estimate that fitted service model's accuracy or replace its reported 345-specimen evaluation. The repeated partitions overlap; their percentiles are descriptive split variability, **not confidence intervals from independent trials**. No pooled specimen-level significance test is used.

The follow-up was proposed after existing evaluation results had been examined. It supplies another view of the development decision, not a new independent validation. Patient and center independence remain unverified. Batch-grouped splitting, assay-QC review and viral-target removal are separate proposed next steps.

For the talk, one figure and the selection counts are sufficient. Keep the frozen model as the demonstrated artifact and explain that logistic is a credible simpler alternative. This follow-up does not justify changing the frozen service by consulting its already-seen author-validation results.

## Reproduce and inspect

```powershell
uv run python -m experiments.rejection_stability.run --output-dir results/followup/new_stability --artifacts-dir data/processed/stability/new_stability
```

New destinations are required; completed runs are never overwritten. The command verifies both public input hashes before fitting. It uses the project lockfile and local Python 3.12 environment. The run took {elapsed:.1f} seconds for 100 candidate fits; every saved candidate reproduced its screening scores within {RELOAD_TOLERANCE:g} after reload.

- [Pre-fit design](design.json), [run manifest](run_manifest.json), and [source snapshot](source/)
- [Candidate screening metrics](screening_metrics.csv), [held-out assessment metrics](assessment_metrics.csv), [family choices](selections.csv), and [paired differences](paired_differences.csv)
- [Editable SVG](model_choice_stability.svg), [PNG](model_choice_stability.png), and the saved CSVs supply editable evidence for a slide.
- Per-specimen assignments/predictions and model binaries are local, Git-ignored artifacts under `{relative(artifacts_dir)}`. Model identities and all artifact hashes are recorded in the run manifest.
"""
    (output_dir / "REPORT.md").write_text(report, encoding="utf-8")


def run(output_dir: Path, artifacts_dir: Path):
    # Abort before creating anything if either destination exists, even if empty.
    if output_dir.exists() or artifacts_dir.exists():
        raise ValueError(
            "Run destinations already exist; choose new output and artifact directories."
        )
    if (
        output_dir == artifacts_dir
        or output_dir.is_relative_to(artifacts_dir)
        or artifacts_dir.is_relative_to(output_dir)
    ):
        raise ValueError("Output and artifact destinations must be separate.")
    if not artifacts_dir.is_relative_to(ROOT / "data/processed/stability"):
        raise ValueError("Specimen artifacts must stay under ignored data/processed/stability.")
    for item in records():
        verify(local_path(item["file"]), item)
    started_at, start_time = datetime.now(timezone.utc).isoformat(), time.perf_counter()
    output_dir.mkdir(parents=True)
    artifacts_dir.mkdir(parents=True)
    config = configuration()
    write_json(output_dir / "design.json", config)
    source_files = [
        Path(__file__),
        ROOT / "experiments/rejection_public/run.py",
        ROOT / "scripts/verify_local_data.py",
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
        ROOT / "tests/test_stability.py",
        *sorted((ROOT / "src/kidney_biopsy").glob("*.py")),
    ]
    for path in source_files:
        destination = output_dir / "source" / path.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    _, metadata = read_geo_matrix(ROOT / "data/raw/rejection_public/GSE212160_series_matrix.txt.gz")
    raw_counts, _ = read_rcc_archive(
        ROOT / "data/raw/rejection_public/GSE212160_RAW.tar", metadata.index
    )
    metadata, features, labels = discovery_data(metadata, raw_counts)
    del raw_counts
    all_screen, all_assessment, selections, class_counts = [], [], [], []
    for repeat, seed in enumerate(SEEDS, 1):
        repeat_dir = artifacts_dir / f"repeat_{repeat:02d}"
        repeat_dir.mkdir()
        parts = split_discovery(metadata, seed)
        assignments = pd.concat(
            [
                pd.DataFrame(
                    {"sample": parts[part], "part": part, "order": range(len(parts[part]))}
                )
                for part in PARTS
            ],
            ignore_index=True,
        )
        assignments["histology"] = metadata.loc[
            assignments["sample"], "histology_diagnosis"
        ].to_numpy()
        assignments.to_csv(repeat_dir / "assignments.csv", index=False)
        for part in PARTS:
            class_counts.append(
                {
                    "repeat": repeat,
                    "seed": seed,
                    "part": part,
                    **metadata.loc[parts[part], "histology_diagnosis"].value_counts().to_dict(),
                }
            )
        models, screen = fit_and_screen(features, labels, parts, config, repeat_dir)
        assessment, selection = freeze_and_assess(
            models,
            screen,
            features,
            labels,
            parts,
            repeat_dir,
            f"{output_dir.name}:repeat_{repeat:02d}",
        )
        all_screen.extend({"repeat": repeat, "seed": seed, **row} for row in screen)
        all_assessment.extend({"repeat": repeat, "seed": seed, **row} for row in assessment)
        selections.append({"repeat": repeat, "seed": seed, **selection})
        print(
            f"Repeat {repeat:02d}/20: selected {selection['selected_model']}; completed {5 * repeat} fits",
            flush=True,
        )
    screen, assessment, selections = (
        pd.DataFrame(all_screen),
        pd.DataFrame(all_assessment),
        pd.DataFrame(selections),
    )
    for filename, frame in (
        ("screening_metrics", screen),
        ("assessment_metrics", assessment),
        ("selections", selections),
        ("class_counts", pd.DataFrame(class_counts)),
    ):
        frame.to_csv(output_dir / f"{filename}.csv", index=False)
    summary, deltas = summarize(assessment, selections)
    write_json(output_dir / "summary.json", summary)
    deltas.to_csv(output_dir / "paired_differences.csv", index=False)
    make_figure(deltas, summary, output_dir)
    elapsed = time.perf_counter() - start_time
    write_report(summary, config, output_dir, artifacts_dir, elapsed)
    files = [*sorted(output_dir.rglob("*")), *sorted(artifacts_dir.rglob("*"))]
    manifest = {
        "started_utc": started_at,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed,
        "python": platform.python_version(),
        "packages": {
            name: version(name)
            for name in (
                "catboost",
                "joblib",
                "matplotlib",
                "numpy",
                "pandas",
                "scikit-learn",
                "scipy",
            )
        },
        "inputs": records(),
        "lock_sha256": sha256(ROOT / "uv.lock"),
        "configuration_sha256": sha256(output_dir / "design.json"),
        "source_import_path": relative(Path(sys.modules["kidney_biopsy"].__file__)),
        "fit_count": len(screen),
        "reload_tolerance": RELOAD_TOLERANCE,
        "reload_max_abs_difference": float(screen.reload_max_abs_difference.max()),
        "artifacts": [
            {"file": relative(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in files
            if path.is_file()
        ],
    }
    write_json(output_dir / "run_manifest.json", manifest)
    print(
        json.dumps({"selection_counts": summary["selection_counts"], "elapsed_seconds": elapsed}),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="results/followup/20260917_stability")
    parser.add_argument("--artifacts-dir", default="data/processed/stability/20260917_stability")
    args = parser.parse_args()
    if (
        Path(sys.modules["kidney_biopsy"].__file__).resolve()
        != ROOT / "src/kidney_biopsy/__init__.py"
    ):
        parser.error("Use the editable project installation: uv sync --locked, then rerun.")
    run(local_path(args.output_dir), local_path(args.artifacts_dir))


if __name__ == "__main__":
    main()
