"""Bounded four-diagnosis follow-up using the preserved discovery split.

Run from this project's root: uv run python experiments/rejection_subtypes/run.py
The technical-validation cohort has already been examined. This is follow-up
analysis, with candidate selection and thresholds restricted to discovery data.
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".uv-cache" / "matplotlib"))

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from verify_local_data import local_path, records, sha256, verify

from kidney_biopsy import (
    AssaySchema,
    map_diagnoses,
    normalize_counts,
    predict_scores,
    read_geo_matrix,
    read_rcc_archive,
)

DIAGNOSES = (
    "No Rejection",
    "Antibody-mediated Rejection",
    "T cell-mediated Rejection",
    "Mixed Rejection",
)
SHORT_NAMES = ("No rejection", "Antibody-mediated", "T-cell-mediated", "Mixed")
TARGETS = ("any_rejection", "antibody_mediated_component", "t_cell_mediated_component")
SPLITS = ("train", "discovery_screen", "author_validation")
LABELS = np.arange(4)
PLOT_NAMES = {
    "four_class_catboost": "Four-class CatBoost",
    "four_class_logistic": "Four-class logistic",
    "separate_components": "Separate components",
    "binary_benchmark": "Binary CatBoost",
}


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def diagnosis_codes(diagnoses: pd.Series) -> pd.Series:
    map_diagnoses(diagnoses)  # Shared rejection of unknown/missing source labels.
    return diagnoses.map({name: i for i, name in enumerate(DIAGNOSES)}).astype(int)


def ordered_class_scores(model, values: pd.DataFrame) -> np.ndarray:
    """Require every diagnosis exactly once and align score columns by class ID."""
    classes = np.asarray(model.classes_)
    if classes.shape != (4,) or set(classes.tolist()) != set(LABELS.tolist()):
        raise ValueError("Four-class model must contain each recorded diagnosis exactly once.")
    score = np.asarray(model.predict_proba(values), dtype=float)
    if (
        score.shape != (len(values), 4)
        or not np.isfinite(score).all()
        or (score < 0).any()
        or (score > 1).any()
        or not np.allclose(score.sum(axis=1), 1, rtol=0, atol=1e-10)
    ):
        raise ValueError("Class scores must be finite, in [0, 1], and sum to one per specimen.")
    return score[:, [int(np.flatnonzero(classes == label)[0]) for label in LABELS]]


def validate_binary_scores(y, score) -> tuple[np.ndarray, np.ndarray]:
    y, score = np.asarray(y), np.asarray(score, dtype=float)
    if y.ndim != 1 or len(y) == 0 or not np.isin(y, [0, 1]).all() or score.shape != y.shape:
        raise ValueError(
            "Binary labels and scores must be matching, nonempty one-dimensional arrays."
        )
    if not np.isfinite(score).all() or (score < 0).any() or (score > 1).any():
        raise ValueError("Binary scores must be finite and between zero and one.")
    return y.astype(int), score


def threshold(y, score, sensitivity: float = 0.90) -> float:
    y, score = validate_binary_scores(y, score)
    if not 0 < sensitivity <= 1 or set(y) != {0, 1}:
        raise ValueError("Threshold selection needs both classes and sensitivity in (0, 1].")
    return float(
        max(
            candidate
            for candidate in np.unique(score)
            if np.mean(score[y == 1] >= candidate) >= sensitivity
        )
    )


def component_diagnoses(
    antibody_score, tcell_score, antibody_threshold: float, tcell_threshold: float
) -> np.ndarray:
    """Both flags means mixed; neither means no rejection. No binary-score gate."""
    antibody_score, tcell_score = np.asarray(antibody_score), np.asarray(tcell_score)
    for values, cutoff in [(antibody_score, antibody_threshold), (tcell_score, tcell_threshold)]:
        validate_binary_scores(np.zeros(values.shape), values)
        if not np.isfinite(cutoff) or not 0 <= cutoff <= 1:
            raise ValueError("Frozen component threshold must be finite and in [0, 1].")
    if antibody_score.shape != tcell_score.shape:
        raise ValueError("Both component scores must cover the same specimens.")
    return (antibody_score >= antibody_threshold).astype(int) + 2 * (
        tcell_score >= tcell_threshold
    ).astype(int)


def validate_split(split: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    if (
        split.empty
        or not split.index.is_unique
        or split.index.isna().any()
        or not metadata.index.is_unique
        or set(split.index) != set(metadata.index)
    ):
        raise ValueError("Saved split and metadata must contain exactly the same unique specimens.")
    if not {"histology", "split"}.issubset(split):
        raise ValueError("Saved split needs original histology and split assignments.")
    split = split.loc[metadata.index]
    diagnosis_codes(split.histology)
    if not np.array_equal(split.histology, metadata.histology_diagnosis):
        raise ValueError("Saved split diagnoses disagree with public source metadata.")
    discovery = metadata.index[metadata.cohort.eq("Discovery cohort sample")]
    evaluation = metadata.index[metadata.cohort.eq("Validation cohort sample")]
    if (len(discovery), len(evaluation)) != (1050, 345):
        raise ValueError("Unexpected author cohort membership or specimen counts.")
    train, screen = train_test_split(
        discovery.to_numpy(),
        test_size=0.25,
        stratify=metadata.loc[discovery, "histology_diagnosis"].to_numpy(),
        random_state=20260915,
    )
    expected = pd.Series("author_validation", index=metadata.index)
    expected.loc[train], expected.loc[screen] = "train", "discovery_screen"
    if not np.array_equal(split.split, expected):
        raise ValueError("Saved split differs from the fixed diagnosis-stratified discovery split.")
    return split


def verified_benchmark_files(run: Path, models: Path) -> tuple[dict, list[Path]]:
    manifest_path = run / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {item["file"]: item for item in manifest["artifacts"]}
    files = [run / "biopsy_split.csv", run / "biopsy_results.json"]
    frozen = {}
    for target in TARGETS:
        path = run / f"{target}_frozen.json"
        files.extend([path, models / f"{target}_selected_model.joblib"])
        # Only read frozen metadata after checking its preserved hash.
        verify(path, expected[relative(path)])
        frozen[target] = json.loads(path.read_text(encoding="utf-8"))
    for path in files:
        if relative(path) not in expected:
            raise ValueError(f"Benchmark run does not record {relative(path)}.")
        verify(path, expected[relative(path)])
    if manifest["input_manifest_sha256"] != sha256(ROOT / "data/manifest.json"):
        raise ValueError("Benchmark used a different public input manifest.")
    return frozen, [manifest_path, *files]


def wilson(successes: int, total: int) -> tuple[float | None, float | None]:
    if total == 0:
        return None, None
    z = 1.959963984540054
    fraction = successes / total
    center = (fraction + z * z / (2 * total)) / (1 + z * z / total)
    width = (
        z
        * np.sqrt(fraction * (1 - fraction) / total + z * z / (4 * total**2))
        / (1 + z * z / total)
    )
    return max(0.0, float(center - width)), min(1.0, float(center + width))


def safe_ratio(a: int, b: int) -> float | None:
    return float(a / b) if b else None


def binary_metrics(y, predicted, score=None, cutoff=None) -> dict:
    y, predicted = np.asarray(y), np.asarray(predicted)
    tn, fp, fn, tp = (int(x) for x in confusion_matrix(y, predicted, labels=[0, 1]).ravel())
    sensitivity_lo, sensitivity_hi = wilson(tp, tp + fn)
    specificity_lo, specificity_hi = wilson(tn, tn + fp)
    return {
        "n": len(y),
        "positives": tp + fn,
        "threshold": cutoff,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "sensitivity": safe_ratio(tp, tp + fn),
        "specificity": safe_ratio(tn, tn + fp),
        "precision": safe_ratio(tp, tp + fp),
        "npv": safe_ratio(tn, tn + fn),
        "accuracy": float(np.mean(y == predicted)),
        "sensitivity_lower": sensitivity_lo,
        "sensitivity_upper": sensitivity_hi,
        "specificity_lower": specificity_lo,
        "specificity_upper": specificity_hi,
        "roc_auc": float(roc_auc_score(y, score)) if score is not None else None,
        "average_precision": float(average_precision_score(y, score))
        if score is not None
        else None,
    }


def subtype_metrics(y, predicted) -> tuple[dict, list[dict], np.ndarray]:
    matrix = confusion_matrix(y, predicted, labels=LABELS)
    classes = []
    for i, diagnosis in enumerate(DIAGNOSES):
        actual_n, predicted_n, correct = (
            int(matrix[i].sum()),
            int(matrix[:, i].sum()),
            int(matrix[i, i]),
        )
        recall_lo, recall_hi = wilson(correct, actual_n)
        precision_lo, precision_hi = wilson(correct, predicted_n)
        classes.append(
            {
                "diagnosis": diagnosis,
                "actual_n": actual_n,
                "predicted_n": predicted_n,
                "correct": correct,
                "missed_class": actual_n - correct,
                "false_class": predicted_n - correct,
                "sensitivity": safe_ratio(correct, actual_n),
                "precision": safe_ratio(correct, predicted_n),
                "sensitivity_lower": recall_lo,
                "sensitivity_upper": recall_hi,
                "precision_lower": precision_lo,
                "precision_upper": precision_hi,
            }
        )
    summary = {
        "n": len(y),
        "accuracy": float(np.mean(np.asarray(y) == predicted)),
        "macro_f1": float(f1_score(y, predicted, labels=LABELS, average="macro", zero_division=0)),
        "correct": int(np.trace(matrix)),
        "incorrect": int(matrix.sum() - np.trace(matrix)),
    }
    return summary, classes, matrix


def marginal_scores(score: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "any_rejection": score[:, 1:].sum(axis=1),
        "antibody_mediated_component": score[:, [1, 3]].sum(axis=1),
        "t_cell_mediated_component": score[:, [2, 3]].sum(axis=1),
    }


def binary_targets(codes: pd.Series) -> dict[str, pd.Series]:
    return {
        "any_rejection": codes.ne(0).astype(int),
        "antibody_mediated_component": codes.isin([1, 3]).astype(int),
        "t_cell_mediated_component": codes.isin([2, 3]).astype(int),
    }


def candidates() -> dict:
    result = {
        f"catboost_depth{depth}": CatBoostClassifier(
            iterations=300,
            depth=depth,
            learning_rate=0.04,
            loss_function="MultiClass",
            random_seed=2026,
            thread_count=3,
            verbose=False,
            allow_writing_files=False,
        )
        for depth in [4, 6]
    }
    for c in [0.01, 0.1, 1.0]:
        result[f"logistic_C{c:g}"] = make_pipeline(
            StandardScaler(), LogisticRegression(C=c, solver="lbfgs", max_iter=3000)
        )
    return result


def fresh_destinations(run: Path, model_dir: Path, case_dir: Path, benchmark: Path) -> None:
    for path in [run, model_dir, case_dir]:
        if path.exists():
            raise ValueError(
                f"Output destination already exists; choose a new directory: {relative(path)}"
            )
    for path in [model_dir, case_dir]:
        if not path.is_relative_to(ROOT / "data/processed"):
            raise ValueError("Models and per-specimen tables must stay in ignored data/processed.")
    paths = [run, model_dir, case_dir, benchmark]
    for i, first in enumerate(paths):
        for second in paths[i + 1 :]:
            if first == second or first in second.parents or second in first.parents:
                raise ValueError("Output, model, case, and benchmark directories must be separate.")


def plot_results(
    out: Path, confusion: pd.DataFrame, any_metrics: pd.DataFrame, mixed: pd.DataFrame
) -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "svg.fonttype": "none",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    figures = out / "figures"
    figures.mkdir()
    validation = confusion[confusion.split.eq("author_validation")]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), constrained_layout=True)
    for ax, model in zip(axes, validation.model.unique()):
        table = (
            validation[validation.model.eq(model)]
            .pivot(index="actual", columns="predicted", values="n")
            .reindex(index=DIAGNOSES, columns=DIAGNOSES)
        )
        matrix = table.to_numpy()
        ax.imshow(matrix, cmap="Blues", vmin=0, vmax=176)
        for i in range(4):
            for j in range(4):
                ax.text(
                    j,
                    i,
                    str(matrix[i, j]),
                    ha="center",
                    va="center",
                    color="white" if matrix[i, j] > 100 else "#18242E",
                )
        ax.set(
            xticks=LABELS,
            yticks=LABELS,
            xticklabels=["None", "Antibody", "T-cell", "Mixed"],
            yticklabels=["None", "Antibody", "T-cell", "Mixed"],
            xlabel="Predicted diagnosis",
            ylabel="Recorded diagnosis",
            title=PLOT_NAMES[model],
        )
    fig.suptitle("Four recorded diagnoses: 345 technical-validation specimens", fontsize=16)
    for suffix in ["svg", "png"]:
        fig.savefig(figures / f"01_subtype_confusion.{suffix}", dpi=170, bbox_inches="tight")
    plt.close(fig)
    rows = any_metrics[any_metrics.split.eq("author_validation")]
    fig, ax = plt.subplots(figsize=(10, 4.8), constrained_layout=True)
    x = np.arange(len(rows))
    for offset, column, label, color in [
        (-0.19, "fn", "Missed rejection / 169", "#B55635"),
        (0.19, "fp", "False flags / 176", "#247C96"),
    ]:
        bars = ax.bar(x + offset, rows[column], width=0.36, label=label, color=color)
        ax.bar_label(bars, padding=3)
    ax.set(
        xticks=x,
        xticklabels=[PLOT_NAMES[name] for name in rows.model],
        ylabel="Specimens",
        ylim=(0, float(rows[["fn", "fp"]].max().max()) + 8),
        title="Any rejection: frozen discovery thresholds on the same 345 specimens",
    )
    ax.legend(loc="upper left", frameon=False)
    for suffix in ["svg", "png"]:
        fig.savefig(figures / f"02_any_rejection_errors.{suffix}", dpi=170, bbox_inches="tight")
    plt.close(fig)
    rows = mixed[mixed.split.eq("author_validation")]
    fig, ax = plt.subplots(figsize=(10, 4.8), constrained_layout=True)
    x = np.arange(len(rows))
    bottom = np.zeros(len(rows))
    for column, label, color in zip(
        ["as_no_rejection", "as_antibody", "as_tcell", "as_mixed"],
        SHORT_NAMES,
        ["#AAB4BC", "#257F9F", "#A16BBD", "#347C5C"],
    ):
        values = rows[column].to_numpy()
        bars = ax.bar(x, values, bottom=bottom, width=0.6, label=label, color=color)
        for bar, value, start in zip(bars, values, bottom):
            if value:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    start + value / 2,
                    str(value),
                    ha="center",
                    va="center",
                    color="white" if column != "as_no_rejection" else "black",
                )
        bottom += values
    ax.set(
        xticks=x,
        xticklabels=[PLOT_NAMES[name] for name in rows.model],
        ylabel="Specimens with recorded mixed rejection",
        ylim=(0, 22),
        title="How each model classified the 18 mixed-rejection specimens",
    )
    ax.legend(ncols=4, loc="upper center", frameon=False)
    for suffix in ["svg", "png"]:
        fig.savefig(figures / f"03_mixed_rejection.{suffix}", dpi=170, bbox_inches="tight")
    plt.close(fig)


def report(
    out: Path, configuration: dict, frozen: dict, tables: dict[str, pd.DataFrame], elapsed: float
) -> None:
    def percent(value):
        return "undefined" if value is None or pd.isna(value) else f"{value:.1%}"

    summaries = tables["subtype_summary"].query("split == 'author_validation'").set_index("model")
    any_rows = (
        tables["any_rejection_metrics"].query("split == 'author_validation'").set_index("model")
    )
    mixed = tables["mixed_rejection"].query("split == 'author_validation'").set_index("model")
    classes = tables["per_class_metrics"].query("split == 'author_validation'")
    counts = tables["class_counts"]
    lines = [
        "# Rejection subtype follow-up",
        "",
        "## Main result",
        "",
        "This follow-up compares four-class CatBoost and multinomial logistic regression with the existing separate component models. "
        "All models score the same specimens directly, including specimens whose binary rejection flag is negative.",
        "",
        "| Model | Correct diagnosis / 345 | Macro F1 | Mixed correctly named / 18 | Any-rejection misses / 169 | False rejection flags / 176 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in summaries.index:
        lines.append(
            f"| {PLOT_NAMES[name]} | {int(summaries.loc[name, 'correct'])} | {summaries.loc[name, 'macro_f1']:.3f} | {int(mixed.loc[name, 'as_mixed'])} | {int(any_rows.loc[name, 'fn'])} | {int(any_rows.loc[name, 'fp'])} |"
        )
    binary = any_rows.loc["binary_benchmark"]
    lines.extend(
        [
            f"| Binary CatBoost benchmark | — | — | — | {int(binary.fn)} | {int(binary.fp)} |",
            "",
            f"The separate component models correctly named {int(mixed.loc['separate_components', 'as_mixed'])} of the 18 mixed diagnoses; "
            f"four-class CatBoost named {int(mixed.loc['four_class_catboost', 'as_mixed'])} and logistic regression named {int(mixed.loc['four_class_logistic', 'as_mixed'])}. "
            f"The corresponding numbers of non-mixed specimens incorrectly called mixed were "
            f"{int(classes.loc[(classes.model.eq('separate_components')) & (classes.diagnosis.eq('Mixed Rejection')), 'false_class'].iloc[0])}, "
            f"{int(classes.loc[(classes.model.eq('four_class_catboost')) & (classes.diagnosis.eq('Mixed Rejection')), 'false_class'].iloc[0])}, and "
            f"{int(classes.loc[(classes.model.eq('four_class_logistic')) & (classes.diagnosis.eq('Mixed Rejection')), 'false_class'].iloc[0])}, respectively.",
            "",
            f"For any rejection, four-class CatBoost missed {int(any_rows.loc['four_class_catboost', 'fn'])} specimens and falsely flagged {int(any_rows.loc['four_class_catboost', 'fp'])}; "
            f"four-class logistic regression missed {int(any_rows.loc['four_class_logistic', 'fn'])} and falsely flagged {int(any_rows.loc['four_class_logistic', 'fp'])}. "
            f"The original binary model missed {int(binary.fn)} and falsely flagged {int(binary.fp)}. "
            "These counts describe the observed tradeoff at each discovery-selected threshold; the four-class comparison supplies no new independent evaluation cohort.",
            "",
            "The four-class diagnosis uses the highest class score. Its any-rejection flag instead uses the sum of all three rejection-class scores and a separately frozen threshold. "
            "Those are different decisions; predicting an incorrect rejection subtype need not mean missing rejection altogether.",
            "",
            "## What changed, and what the comparison can establish",
            "",
            "The primary binary model remains the research service model. These subtype results describe an additional label task; "
            "they do not replace the binary model or its threshold. This is follow-up analysis because the authors' technical-validation cohort "
            "was examined in earlier project work. No validation result selected a candidate or changed a threshold in this run. Independent confirmation requires a new cohort.",
            "",
            "## Discovery selection",
            "",
            "Five candidates were fixed before fitting: four-class CatBoost with depths 4 and 6, 300 trees, learning rate 0.04 and seed 2026; "
            "and full-panel multinomial logistic regression with C = 0.01, 0.1, and 1. StandardScaler was fitted on training rows only. "
            "The logistic model uses the multinomial loss with the lbfgs solver, as described in the "
            "[scikit-learn documentation](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html).",
            "",
            "Within each family, maximize discovery-screen macro F1 (the mean of each diagnosis's F1), then accuracy; exact ties favor lower depth or stronger regularization. "
            "This weights mixed rejection equally in selection even though it is uncommon. The selected fitted model is retained without refitting. "
            "The entire bounded candidate grid is in `configuration.json`; all screening results are in `candidate_screen.csv`.",
            "",
        ]
    )
    for family, item in frozen["four_class_models"].items():
        lines.append(
            f"- {PLOT_NAMES[family]}: **{item['candidate']}**, discovery macro F1 {item['screen']['macro_f1']:.3f}; any-rejection threshold {item['thresholds']['any_rejection']:.12g}."
        )
    lines.extend(
        [
            "",
            "Each sum-of-rejection threshold is the highest screening score that retains at least 90% of screening rejection cases, matching the original binary operating rule. "
            "Antibody and T-cell marginal-score thresholds use that same rule on their own component labels. Threshold selection does not establish probability calibration; "
            "outputs remain model scores. Separate-component thresholds and models are preserved from the benchmark run.",
            "",
            "## Same specimens and preprocessing",
            "",
            "| Split | No rejection | Antibody-mediated | T-cell-mediated | Mixed | Total |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for split in SPLITS:
        row = counts[counts.split.eq(split)].set_index("diagnosis").n
        lines.append(
            f"| {split} | "
            + " | ".join(str(int(row[name])) for name in DIAGNOSES)
            + f" | {int(row.sum())} |"
        )
    lines.extend(
        [
            "",
            "The raw GSE212160 RCC measurements are read through the shared source reader. Each specimen is transformed by log2(count + 1), "
            "then subtracting its mean across the 12 housekeeping targets. The remaining 758 assay targets are used in the frozen order. "
            "Recorded diagnoses, cohort, specimen IDs, and assay batch fields are excluded from predictors. The saved split is matched by specimen ID, "
            "checked against the source diagnoses and author cohorts, and checked against the exact seed-20260915 diagnosis-stratified split. "
            "The original raw files, saved split, frozen benchmark metadata and model files are hash-verified before use. See `data_audit.json`.",
            "",
            "## Per-class results on technical validation",
            "",
            "Sensitivity means the fraction of that recorded diagnosis correctly named. Precision means the fraction of that predicted diagnosis that was correct. "
            "Intervals are 95% Wilson intervals over biopsy specimens; patient independence is not established.",
            "",
            "| Model | Diagnosis | Correct / actual | Predicted | Sensitivity (95% interval) | Precision (95% interval) |",
            "| --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for row in classes.itertuples(index=False):
        lines.append(
            f"| {PLOT_NAMES[row.model]} | {row.diagnosis} | {row.correct}/{row.actual_n} | {row.predicted_n} | {percent(row.sensitivity)} ({percent(row.sensitivity_lower)}–{percent(row.sensitivity_upper)}) | {percent(row.precision)} ({percent(row.precision_lower)}–{percent(row.precision_upper)}) |"
        )
    lines.extend(
        [
            "",
            "All four-by-four counts, including zeros, are in `confusion_matrices.csv` and the [editable confusion chart](figures/01_subtype_confusion.svg).",
            "",
            "## Mixed rejection",
            "",
            "| Model | Predicted none | Predicted antibody only | Predicted T-cell only | Predicted mixed |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for name, row in mixed.iterrows():
        lines.append(
            f"| {PLOT_NAMES[name]} | {int(row.as_no_rejection)} | {int(row.as_antibody)} | {int(row.as_tcell)} | {int(row.as_mixed)} |"
        )
    lines.extend(
        [
            "",
            "The separate-component prediction is mixed only when both preserved component flags are positive; antibody only and T-cell only require the corresponding flag alone. "
            "Neither flag produces no rejection. This is a direct four-diagnosis comparison and does not assume the two component scores are independent probabilities. "
            "For four-class models, `component_metrics.csv` also evaluates antibody-plus-mixed and T-cell-plus-mixed score sums with discovery-chosen component thresholds. "
            "The distinction shows whether a mixed specimen is missing one component or whether the four-way choice assigned it to a single-component diagnosis. "
            "Only 18 validation specimens have mixed rejection; the intervals above reflect the limited number.",
            "",
            "## Any-rejection comparison",
            "",
            "| Model | Threshold | Sensitivity | Specificity | Misses | False flags | Misses minus binary | False flags minus binary |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for name, row in any_rows.iterrows():
        cutoff = "Either component flag" if pd.isna(row.threshold) else f"{row.threshold:.6f}"
        lines.append(
            f"| {PLOT_NAMES[name]} | {cutoff} | {percent(row.sensitivity)} | {percent(row.specificity)} | {int(row.fn)} | {int(row.fp)} | {int(row.fn - binary.fn):+d} | {int(row.fp - binary.fp):+d} |"
        )
    lines.extend(
        [
            "",
            "The 90% sensitivity setting applied to discovery screening; it does not guarantee 90% sensitivity in technical validation. "
            "`any_rejection_metrics.csv` includes screening and validation counts, intervals, precision, negative predictive value, ROC-AUC, and average precision. "
            "No single continuous any-rejection score is asserted for the union of the two separate component flags, so its ROC-AUC and average precision are left undefined. "
            "`any_errors_by_diagnosis.csv` separates false flags and misses by the original diagnosis. `paired_error_differences.csv` contains paired specimen-bootstrap intervals "
            "for differences in missed rejection and false flags, with 2,000 resamples and seed 20260915. These are descriptive specimen intervals, not evidence of patient-level independence.",
            "",
            "## Reproduce and inspect",
            "",
            "From the project root:",
            "",
            "```powershell",
            "uv sync --locked",
            "uv run python scripts/verify_local_data.py",
            "uv run python experiments/rejection_subtypes/run.py",
            "```",
            "",
            "For a clean checkout, run the documented download and binary-reproduction commands first. This follow-up uses the independently generated "
            f"`{configuration['benchmark_run']}` run and `{configuration['benchmark_models']}` models. Populated local inputs need no download. "
            "Completed outputs are never overwritten: set fresh `--output-dir`, `--model-dir`, and `--case-dir` for another run. "
            "Use `--benchmark-run` and `--benchmark-models` to name another fixed reproduction.",
            "",
            f"This run fitted five candidates in {elapsed:.1f} seconds including input verification, fitting, evaluation and chart preparation. "
            "`run_manifest.json` records exact elapsed time, package versions, input/output hashes, source snapshots and the lockfile used at run start. "
            "`frozen.json` was written before technical-validation predictions. New model save/reload scores agree within an absolute tolerance of 1e-12, "
            "with actual maximum differences in `verification.json`; benchmark scores also reproduce their saved prediction tables within that tolerance.",
            "",
            "Editable evidence: [confusion matrices](figures/01_subtype_confusion.svg), [any-rejection errors](figures/02_any_rejection_errors.svg), "
            "and [mixed-rejection predictions](figures/03_mixed_rejection.svg). Each has a PNG and an aggregate CSV. "
            "Per-specimen scores and error tables are kept only in the ignored case directory, and fitted models only in the ignored model directory.",
            "",
        ]
    )
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-run", default="results/reproduction/20260915_shared")
    parser.add_argument("--benchmark-models", default="data/processed/models/20260915_shared")
    parser.add_argument("--output-dir", default="results/followup/20260915_subtypes")
    parser.add_argument("--model-dir", default="data/processed/models/20260915_subtypes")
    parser.add_argument("--case-dir", default="data/processed/analysis/20260915_subtypes")
    args = parser.parse_args()
    benchmark, benchmark_models, out, model_dir, case_dir = [
        local_path(value)
        for value in [
            args.benchmark_run,
            args.benchmark_models,
            args.output_dir,
            args.model_dir,
            args.case_dir,
        ]
    ]
    fresh_destinations(out, model_dir, case_dir, benchmark)
    started = datetime.now(timezone.utc).isoformat()
    start = time.perf_counter()
    raw_records = records()
    for item in raw_records:
        verify(local_path(item["file"]), item)
    benchmark_frozen, input_paths = verified_benchmark_files(benchmark, benchmark_models)
    for path in [out, model_dir, case_dir]:
        path.mkdir(parents=True)
    configuration = {
        "analysis_type": "Follow-up; technical-validation results were already examined in prior work.",
        "benchmark_run": args.benchmark_run,
        "benchmark_models": args.benchmark_models,
        "output_dir": args.output_dir,
        "model_dir": args.model_dir,
        "case_dir": args.case_dir,
        "diagnosis_order": list(DIAGNOSES),
        "discovery_split_seed": 20260915,
        "preprocessing": "Shared raw readers and log2(count+1) minus the specimen mean across 12 housekeeping targets; 758 assay predictors.",
        "catboost_grid": {
            "depth": [4, 6],
            "iterations": 300,
            "learning_rate": 0.04,
            "loss_function": "MultiClass",
            "random_seed": 2026,
            "thread_count": 3,
        },
        "logistic_grid": {
            "C": [0.01, 0.1, 1.0],
            "solver": "lbfgs",
            "max_iter": 3000,
            "scaler": "StandardScaler fitted on training only",
            "loss": "multinomial",
            "penalty": "L2",
        },
        "selection": "Within each family maximize screening macro F1, then accuracy; exact ties use lower depth or lower C. No refit.",
        "threshold_rule": "For each any-rejection or component score, highest screening threshold retaining >=90% of that target's positives.",
        "diagnosis_rule": "Highest four-class score; ties use diagnosis_order. No binary flag gate.",
        "separate_component_rule": "Use existing component models and thresholds: neither=none, antibody only=antibody, T-cell only=T-cell, both=mixed.",
        "bootstrap": {
            "replicates": 2000,
            "seed": 20260915,
            "unit": "biopsy specimen",
            "scheme": "paired nonparametric percentile",
        },
    }
    write_json(out / "configuration.json", configuration)
    # Snapshot only the code used by this analysis; the application can evolve independently.
    source_paths = [
        Path(__file__),
        ROOT / "scripts/verify_local_data.py",
        ROOT / "tests/test_subtypes.py",
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
        *[
            ROOT / "src/kidney_biopsy" / name
            for name in ["__init__.py", "preprocessing.py", "source.py", "prediction.py"]
        ],
    ]
    snapshots = []
    for path in source_paths:
        destination = out / "source" / path.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        snapshots.append(
            {
                "file": relative(path),
                "snapshot": relative(destination),
                "sha256": sha256(destination),
            }
        )
    raw = ROOT / "data/raw/rejection_public"
    _, metadata = read_geo_matrix(raw / "GSE212160_series_matrix.txt.gz")
    split = validate_split(
        pd.read_csv(benchmark / "biopsy_split.csv", index_col="sample"), metadata
    )
    counts, _ = read_rcc_archive(raw / "GSE212160_RAW.tar", specimen_ids=metadata.index)
    features = normalize_counts(counts)
    if features.shape != (1395, 758):
        raise ValueError("Expected exactly 1,395 specimens and 758 normalized assay targets.")
    schema = AssaySchema(features=tuple(features.columns))
    for frozen in benchmark_frozen.values():
        if schema.to_dict() != frozen["schema"]:
            raise ValueError("Subtype preprocessing schema disagrees with benchmark schema.")
    profile_hash = pd.util.hash_pandas_object(features, index=False)
    if (
        pd.DataFrame({"hash": profile_hash, "split": split.split})
        .groupby("hash")
        .split.nunique()
        .gt(1)
        .any()
    ):
        raise ValueError("Identical molecular profiles cross the saved splits.")
    split.to_csv(case_dir / "biopsy_split.csv", index_label="sample")
    class_counts = (
        pd.crosstab(split.split, split.histology)
        .reindex(index=SPLITS, columns=DIAGNOSES)
        .stack()
        .rename("n")
        .reset_index()
        .rename(columns={"histology": "diagnosis"})
    )
    write_json(
        out / "data_audit.json",
        {
            "specimens": len(features),
            "excluded": 0,
            "features": len(features.columns),
            "duplicates": int(features.duplicated(keep=False).sum()),
            "cross_split_duplicate_profiles": 0,
            "split_matches_saved_and_recomputed": True,
            "source_labels_match_saved_split": True,
            "normalization_schema_matches_all_benchmarks": True,
            "class_counts": class_counts.to_dict(orient="records"),
        },
    )
    codes = diagnosis_codes(split.histology)
    targets = binary_targets(codes)
    ids = {name: split.index[split.split.eq(name)] for name in SPLITS}
    all_candidates, screens = candidates(), []
    screen_scores = {}
    for name, model in all_candidates.items():
        fit_start = time.perf_counter()
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            model.fit(features.loc[ids["train"]], codes.loc[ids["train"]])
        score = ordered_class_scores(model, features.loc[ids["discovery_screen"]])
        screen_scores[name] = score
        summary, _, _ = subtype_metrics(
            codes.loc[ids["discovery_screen"]].to_numpy(), score.argmax(axis=1)
        )
        screening = {
            "candidate": name,
            "family": "four_class_catboost"
            if name.startswith("catboost")
            else "four_class_logistic",
            **summary,
            "seconds": time.perf_counter() - fit_start,
        }
        screens.append(screening)
        print("SCREEN", json.dumps(screening), flush=True)
    frozen = {
        "written_utc": datetime.now(timezone.utc).isoformat(),
        "four_class_models": {},
        "benchmark_run": args.benchmark_run,
        "benchmark_models": benchmark_frozen,
        "selection": configuration["selection"],
        "schema": schema.to_dict(),
        "class_order": list(DIAGNOSES),
    }
    for family in ["four_class_catboost", "four_class_logistic"]:
        # Stable candidate insertion order implements the documented simplicity tie-break.
        selected = max(
            [row for row in screens if row["family"] == family],
            key=lambda row: (row["macro_f1"], row["accuracy"]),
        )
        name = selected["candidate"]
        cutoffs = {
            target: threshold(targets[target].loc[ids["discovery_screen"]], score)
            for target, score in marginal_scores(screen_scores[name]).items()
        }
        path = model_dir / f"{family}.joblib"
        joblib.dump(all_candidates[name], path)
        frozen["four_class_models"][family] = {
            "candidate": name,
            "thresholds": cutoffs,
            "screen": selected,
            "model_file": relative(path),
            "model_sha256": sha256(path),
            "model_version": f"{out.name}:{name}",
        }
    write_json(out / "frozen.json", frozen)
    frozen_hash = sha256(out / "frozen.json")
    pd.DataFrame(screens).to_csv(out / "candidate_screen.csv", index=False)
    print(
        "FROZEN",
        json.dumps(
            {family: item["candidate"] for family, item in frozen["four_class_models"].items()}
        ),
        flush=True,
    )

    # All model choices and thresholds are now fixed; begin validation scoring.
    benchmark_models_loaded = {
        target: joblib.load(benchmark_models / f"{target}_selected_model.joblib")
        for target in TARGETS
    }
    selected_models = {
        family: joblib.load(local_path(item["model_file"]))
        for family, item in frozen["four_class_models"].items()
    }
    verification = {
        "frozen_before_validation_scores": True,
        "frozen_sha256": frozen_hash,
        "score_absolute_tolerance": 1e-12,
        "model_reload_max_absolute_difference": {},
        "benchmark_saved_score_max_absolute_difference": {},
    }
    summary_rows, class_rows, confusion_rows, any_rows, component_rows, mixed_rows, error_rows = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    validation_flags = {}
    for split_name in ["discovery_screen", "author_validation"]:
        index = ids[split_name]
        truth = codes.loc[index].to_numpy()
        binary_truth = truth != 0
        case = pd.DataFrame(
            {"histology": split.loc[index, "histology"], "diagnosis_code": truth}, index=index
        )
        four_scores = {}
        four_predictions = {}
        any_predictions = {}
        for family, model in selected_models.items():
            score = ordered_class_scores(model, features.loc[index])
            original = ordered_class_scores(
                all_candidates[frozen["four_class_models"][family]["candidate"]],
                features.loc[index],
            )
            maximum = float(np.max(np.abs(score - original)))
            if not np.allclose(score, original, rtol=0, atol=1e-12):
                raise ValueError("Four-class model scores changed after serialization.")
            verification["model_reload_max_absolute_difference"][f"{split_name}:{family}"] = maximum
            four_scores[family] = score
            four_predictions[family] = score.argmax(axis=1)
            case[f"{family}_diagnosis"] = [DIAGNOSES[label] for label in four_predictions[family]]
            for i, diagnosis in enumerate(DIAGNOSES):
                case[f"{family}_{diagnosis}_score"] = score[:, i]
            for target, marginal in marginal_scores(score).items():
                cutoff = frozen["four_class_models"][family]["thresholds"][target]
                predicted = marginal >= cutoff
                result = {
                    "split": split_name,
                    "model": family,
                    "target": target,
                    **binary_metrics(targets[target].loc[index], predicted, marginal, cutoff),
                }
                (any_rows if target == "any_rejection" else component_rows).append(result)
                case[f"{family}_{target}_score"] = marginal
                case[f"{family}_{target}_flag"] = predicted
                if target == "any_rejection":
                    any_predictions[family] = predicted
        component_scores = {}
        for target, model in benchmark_models_loaded.items():
            score = predict_scores(model, features.loc[index])
            cutoff = benchmark_frozen[target]["threshold"]
            predicted = score >= cutoff
            name = "binary_benchmark" if target == "any_rejection" else "separate_components"
            result = {
                "split": split_name,
                "model": name,
                "target": target,
                **binary_metrics(targets[target].loc[index], predicted, score, cutoff),
            }
            (any_rows if target == "any_rejection" else component_rows).append(result)
            case[f"benchmark_{target}_score"], case[f"benchmark_{target}_flag"] = score, predicted
            if target == "any_rejection":
                any_predictions[name] = predicted
            else:
                component_scores[target] = score
            suffix = "screen" if split_name == "discovery_screen" else "test"
            saved_path = (
                benchmark
                / f"{target}_{benchmark_frozen[target]['selected_model']}_{suffix}_predictions.csv"
            )
            input_paths.append(saved_path)
            manifest = json.loads((benchmark / "run_manifest.json").read_text(encoding="utf-8"))
            expected = {item["file"]: item for item in manifest["artifacts"]}
            verify(saved_path, expected[relative(saved_path)])
            saved = pd.read_csv(saved_path, index_col="sample")
            if not saved.index.is_unique or set(saved.index) != set(index):
                raise ValueError("Benchmark saved predictions do not match the current specimens.")
            saved = saved.loc[index]
            score_column = "rejection_score" if suffix == "screen" else "probability"
            maximum = float(np.max(np.abs(saved[score_column].to_numpy() - score)))
            if not np.array_equal(saved.y, targets[target].loc[index]) or not np.allclose(
                saved[score_column], score, rtol=0, atol=1e-12
            ):
                raise ValueError("Benchmark scores or labels differ from the preserved run.")
            verification["benchmark_saved_score_max_absolute_difference"][
                f"{split_name}:{target}"
            ] = maximum
        combined = component_diagnoses(
            component_scores["antibody_mediated_component"],
            component_scores["t_cell_mediated_component"],
            benchmark_frozen["antibody_mediated_component"]["threshold"],
            benchmark_frozen["t_cell_mediated_component"]["threshold"],
        )
        four_predictions["separate_components"] = combined
        any_predictions["separate_components"] = combined != 0
        case["separate_components_diagnosis"] = [DIAGNOSES[label] for label in combined]
        any_rows.append(
            {
                "split": split_name,
                "model": "separate_components",
                "target": "any_rejection",
                **binary_metrics(binary_truth, combined != 0),
            }
        )
        for model, prediction in four_predictions.items():
            summary, classes, matrix = subtype_metrics(truth, prediction)
            summary_rows.append({"split": split_name, "model": model, **summary})
            class_rows.extend({"split": split_name, "model": model, **row} for row in classes)
            confusion_rows.extend(
                {
                    "split": split_name,
                    "model": model,
                    "actual": DIAGNOSES[i],
                    "predicted": DIAGNOSES[j],
                    "n": int(matrix[i, j]),
                }
                for i in range(4)
                for j in range(4)
            )
            mixed_rows.append(
                {
                    "split": split_name,
                    "model": model,
                    "actual_mixed": int(matrix[3].sum()),
                    **{
                        key: int(matrix[3, i])
                        for i, key in enumerate(
                            ["as_no_rejection", "as_antibody", "as_tcell", "as_mixed"]
                        )
                    },
                }
            )
        for model, prediction in any_predictions.items():
            for i, diagnosis in enumerate(DIAGNOSES):
                mask = truth == i
                error_rows.append(
                    {
                        "split": split_name,
                        "model": model,
                        "diagnosis": diagnosis,
                        "n": int(mask.sum()),
                        "errors": int(np.sum(prediction[mask] != (i != 0))),
                        "error_type": "false_flag" if i == 0 else "missed_rejection",
                    }
                )
        if split_name == "author_validation":
            validation_flags = any_predictions
        case.to_csv(case_dir / f"{split_name}_scores.csv", index_label="sample")
    if sha256(out / "frozen.json") != frozen_hash:
        raise ValueError("Frozen configuration changed during evaluation.")
    write_json(out / "verification.json", verification)
    difference_rows = []
    rng = np.random.default_rng(20260915)
    truth = targets["any_rejection"].loc[ids["author_validation"]].to_numpy()
    bootstrap_indices = rng.integers(0, len(truth), size=(2000, len(truth)))
    baseline = validation_flags["binary_benchmark"]
    for name, flags in validation_flags.items():
        if name == "binary_benchmark":
            continue
        for metric, target_value, error_value in [
            ("missed_rejection", 1, False),
            ("false_flags", 0, True),
        ]:
            difference = ((truth == target_value) & (flags == error_value)).astype(int) - (
                (truth == target_value) & (baseline == error_value)
            ).astype(int)
            draws = difference[bootstrap_indices].sum(axis=1)
            lower, upper = np.quantile(draws, [0.025, 0.975])
            difference_rows.append(
                {
                    "model": name,
                    "reference": "binary_benchmark",
                    "metric": metric,
                    "estimate": int(difference.sum()),
                    "lower": float(lower),
                    "upper": float(upper),
                    "resamples": 2000,
                }
            )
    tables = {
        "class_counts": class_counts,
        "subtype_summary": pd.DataFrame(summary_rows),
        "per_class_metrics": pd.DataFrame(class_rows),
        "confusion_matrices": pd.DataFrame(confusion_rows),
        "any_rejection_metrics": pd.DataFrame(any_rows),
        "component_metrics": pd.DataFrame(component_rows),
        "mixed_rejection": pd.DataFrame(mixed_rows),
        "any_errors_by_diagnosis": pd.DataFrame(error_rows),
        "paired_error_differences": pd.DataFrame(difference_rows),
    }
    for name, table in tables.items():
        table.to_csv(out / f"{name}.csv", index=False)
    plot_results(
        out,
        tables["confusion_matrices"],
        tables["any_rejection_metrics"],
        tables["mixed_rejection"],
    )
    elapsed = time.perf_counter() - start
    report(out, configuration, frozen, tables, elapsed)
    artifacts = [
        {"file": relative(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for directory in [out, model_dir, case_dir]
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    ]
    write_json(
        out / "run_manifest.json",
        {
            "analysis_type": configuration["analysis_type"],
            "started_utc": started,
            "finished_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": time.perf_counter() - start,
            "python": platform.python_version(),
            "dependencies": {
                name: version(name)
                for name in [
                    "catboost",
                    "joblib",
                    "numpy",
                    "pandas",
                    "scikit-learn",
                    "scipy",
                    "matplotlib",
                ]
            },
            "sources": snapshots,
            "raw_sources": raw_records,
            "inputs": [{"file": relative(path), "sha256": sha256(path)} for path in input_paths],
            "input_manifest_sha256": sha256(ROOT / "data/manifest.json"),
            "fit_count": 5,
            "environment_lock": next(row for row in snapshots if row["file"] == "uv.lock"),
            "artifacts": artifacts,
        },
    )
    print(
        f"COMPLETE: {relative(out / 'REPORT.md')}; {time.perf_counter() - start:.1f} seconds",
        flush=True,
    )


if __name__ == "__main__":
    main()
