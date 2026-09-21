"""Describe a completed frozen run; never fit models or change thresholds.

Run from the project root: uv run python scripts/analyze_results.py
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".uv-cache" / "matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter
from sklearn.metrics import (
    average_precision_score,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)

from kidney_biopsy.prediction import project_path as checked_project_path
from kidney_biopsy.prediction import sha256
from kidney_biopsy.preprocessing import DIAGNOSES, map_diagnoses

SHORT_DIAGNOSES = [
    "No rejection\n(false flags)",
    "Antibody-mediated\n(misses)",
    "T cell-mediated\n(misses)",
    "Mixed\n(misses)",
]
SPLITS = ["train", "discovery_screen", "author_validation"]
METADATA = ["Date", "CartridgeID", "ScannerID"]
SEED = 20260915
BOOTSTRAPS = 2000
COLORS = ["#176D8A", "#D37B21", "#7B58A3", "#737D85"]
METRICS = [
    "sensitivity",
    "specificity",
    "ppv",
    "npv",
    "roc_auc",
    "average_precision",
    "accuracy",
    "brier",
    "mean_score",
    "fn",
    "fp",
]
DIFFERENCES = ["sensitivity", "specificity", "roc_auc", "brier", "fn", "fp"]


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def project_path(value: str) -> Path:
    return checked_project_path(ROOT, value)


def binary_labels(histology: pd.Series) -> pd.Series:
    return map_diagnoses(histology)


def unique_index(frame: pd.DataFrame, name: str) -> None:
    if frame.empty or frame.index.isna().any() or frame.index.has_duplicates:
        raise ValueError(f"{name} has empty, missing, or duplicate specimen IDs")


def align_predictions(
    frame: pd.DataFrame, reference: pd.DataFrame, threshold: float
) -> pd.DataFrame:
    """Require exactly the evaluation rows, their labels, and frozen decisions."""
    unique_index(frame, "Predictions")
    unique_index(reference, "Evaluation split")
    if set(frame.index) != set(reference.index):
        raise ValueError("Predictions and evaluation split contain different specimens")
    if not {"y", "probability", "predicted"}.issubset(frame):
        raise ValueError("Saved predictions lack required columns")
    result = frame.loc[reference.index].copy()
    expected_labels = binary_labels(reference.histology).to_numpy()
    if not np.array_equal(result.y.to_numpy(), expected_labels):
        raise ValueError("Saved prediction labels disagree with original diagnoses")
    score = pd.to_numeric(result.probability, errors="raise").to_numpy(dtype=float)
    if not np.isfinite(score).all() or (score < 0).any() or (score > 1).any():
        raise ValueError("Saved scores must be finite and between zero and one")
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Invalid frozen threshold")
    # Do not convert the string 'False' with astype(bool).
    boolean_values = {"true": True, "false": False, "1": True, "0": False}
    decisions = result.predicted.astype(str).str.lower().map(boolean_values)
    if decisions.isna().any() or not np.array_equal(decisions.to_numpy(), score >= threshold):
        raise ValueError("Saved decisions disagree with the frozen threshold")
    result["probability"] = score
    result["predicted"] = decisions.to_numpy(dtype=bool)
    return result


def ratio(numerator: int, denominator: int) -> float:
    return float(numerator / denominator) if denominator else float("nan")


def metrics(y: np.ndarray, score: np.ndarray, threshold: float) -> dict:
    """Evaluate a fixed score and threshold against recorded binary diagnoses."""
    predicted = score >= threshold
    positive = y == 1
    tp = int(np.sum(positive & predicted))
    fn = int(np.sum(positive & ~predicted))
    fp = int(np.sum(~positive & predicted))
    tn = int(np.sum(~positive & ~predicted))
    both_classes_present = len(np.unique(y)) == 2
    return {
        "n": len(y),
        "positives": int(positive.sum()),
        "negatives": int((~positive).sum()),
        "prevalence": float(y.mean()),
        "threshold": threshold,
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "sensitivity": ratio(tp, tp + fn),
        "specificity": ratio(tn, tn + fp),
        "ppv": ratio(tp, tp + fp),
        "npv": ratio(tn, tn + fn),
        "accuracy": ratio(tp + tn, len(y)),
        "roc_auc": float(roc_auc_score(y, score)) if both_classes_present else float("nan"),
        "average_precision": (
            float(average_precision_score(y, score)) if positive.any() else float("nan")
        ),
        "brier": float(np.mean((score - y) ** 2)),
        "mean_score": float(score.mean()),
    }


def wilson(successes: int, n: int) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    z = 1.959963984540054
    p = successes / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    radius = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def reliability(y: np.ndarray, score: np.ndarray, model: str) -> list[dict]:
    """Ten fixed equal-width bins: [0,.1), ... [.9,1], retaining empty bins."""
    bins = np.minimum((score * 10).astype(int), 9)
    records = []
    for bin_index in range(10):
        mask = bins == bin_index
        n = int(mask.sum())
        positives = int(y[mask].sum())
        lower, upper = wilson(positives, n)
        records.append(
            {
                "model": model,
                "bin": bin_index + 1,
                "lower_edge": bin_index / 10,
                "upper_edge": (bin_index + 1) / 10,
                "n": n,
                "positives": positives,
                "mean_score": float(score[mask].mean()) if n else np.nan,
                "observed_fraction": ratio(positives, n),
                "wilson_lower": lower,
                "wilson_upper": upper,
            }
        )
    return records


def paired_bootstrap(
    y: np.ndarray,
    scores: dict[str, np.ndarray],
    thresholds: dict[str, float],
    n_bootstrap: int,
    seed: int,
) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Sample specimen positions once per replicate and apply them to every model."""
    if n_bootstrap < 2:
        raise ValueError("At least two bootstrap replicates are required")
    rng = np.random.default_rng(seed)
    samples = {name: np.full((n_bootstrap, len(METRICS)), np.nan) for name in scores}
    point = {name: metrics(y, score, thresholds[name]) for name, score in scores.items()}

    # Every model sees the same resampled specimens in each replicate.
    for replicate in range(n_bootstrap):
        positions = rng.integers(0, len(y), len(y))
        for name, score in scores.items():
            result = metrics(y[positions], score[positions], thresholds[name])
            samples[name][replicate] = [result[key] for key in METRICS]

    # First summarize each model, then the paired differences from the selected model.
    intervals = []
    for name, values in samples.items():
        for column, metric in enumerate(METRICS):
            draws = values[:, column]
            valid = draws[np.isfinite(draws)]
            lower, upper = np.quantile(valid, [0.025, 0.975]) if len(valid) else (np.nan, np.nan)
            intervals.append(
                {
                    "model": name,
                    "metric": metric,
                    "estimate": point[name][metric],
                    "lower": lower,
                    "upper": upper,
                    "valid_replicates": len(valid),
                }
            )

    selected = next(iter(scores))
    differences = []
    for other in scores:
        if other in [selected, "training_prevalence"]:
            continue
        for metric in DIFFERENCES:
            column = METRICS.index(metric)
            paired_difference = samples[selected][:, column] - samples[other][:, column]
            valid = paired_difference[np.isfinite(paired_difference)]
            lower, upper = np.quantile(valid, [0.025, 0.975]) if len(valid) else (np.nan, np.nan)
            differences.append(
                {
                    "model": selected,
                    "minus_model": other,
                    "metric": metric,
                    "estimate": point[selected][metric] - point[other][metric],
                    "lower": lower,
                    "upper": upper,
                    "valid_replicates": len(valid),
                }
            )
    return point, pd.DataFrame(intervals), pd.DataFrame(differences)


def load_run(run: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict, dict, list[Path], dict]:
    """Align saved specimens and predictions, then verify their recorded provenance."""
    split_path = run / "biopsy_split.csv"
    batch_path = run / "raw_batch_identifiers.csv"
    result_path = run / "biopsy_results.json"
    frozen_path = run / "any_rejection_frozen.json"
    manifest_path = run / "run_manifest.json"
    inputs = [split_path, batch_path, result_path, frozen_path, manifest_path]

    split = pd.read_csv(split_path, dtype={"sample": str}).set_index("sample")
    unique_index(split, "Saved split")
    binary_labels(split.histology)
    if split.split.isna().any() or set(split.split) != set(SPLITS):
        raise ValueError("Expected train, discovery_screen, and author_validation splits")
    batch = pd.read_csv(batch_path, index_col=0, dtype=str)
    unique_index(batch, "Assay metadata")
    if set(batch.index) != set(split.index) or not set(METADATA).issubset(batch):
        raise ValueError("Assay metadata and saved split differ in rows or required fields")
    split = split.join(batch[METADATA].fillna("Missing"), validate="one_to_one")
    result = json.loads(result_path.read_text())["any_rejection"]
    frozen = json.loads(frozen_path.read_text())
    selected = result["selected_model"]
    evaluation_results = result["author_validation"]
    if (
        frozen["selected_model"] != selected
        or frozen["threshold"] != evaluation_results[selected]["threshold"]
    ):
        raise ValueError("Frozen model metadata and saved results disagree")
    evaluation = split.loc[split.split == "author_validation"].copy()
    y = binary_labels(evaluation.histology).to_numpy()
    scores = {}
    thresholds = {}
    for name in dict.fromkeys([selected, "logistic_all", "single_gene_IFNG"]):
        path = run / f"any_rejection_{name}_test_predictions.csv"
        inputs.append(path)
        threshold = evaluation_results[name]["threshold"]
        saved_predictions = pd.read_csv(path, dtype={"sample": str}).set_index("sample")
        frame = align_predictions(saved_predictions, evaluation, threshold)
        scores[name] = frame.probability.to_numpy()
        thresholds[name] = threshold
    training_labels = binary_labels(split.loc[split.split == "train", "histology"])
    scores["training_prevalence"] = np.full(len(evaluation), training_labels.mean())
    thresholds["training_prevalence"] = 0.5
    for name, score in scores.items():
        computed = metrics(y, score, thresholds[name])
        saved = evaluation_results[name]
        for key in ["n", "positives", "tp", "fn", "fp", "tn", "roc_auc", "brier"]:
            if not np.isclose(computed[key], saved[key], atol=1e-12, rtol=0):
                raise ValueError(f"Recomputed {name} {key} disagrees with saved results")
    manifest = json.loads(manifest_path.read_text())
    recorded = {item["file"]: item for item in manifest["artifacts"]}
    for path in inputs:
        if path.name == "run_manifest.json":
            continue
        item = recorded.get(relative(path))
        if item is None or sha256(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
            raise ValueError(f"Saved input fails completed-run manifest check: {relative(path)}")
    source_manifest = project_path(manifest["input_manifest"])
    if sha256(source_manifest) != manifest["input_manifest_sha256"]:
        raise ValueError("Public-source manifest differs from the completed training run")
    # Predictions are the analysis inputs, but also verify the run's physical raw sources.
    for item in json.loads(source_manifest.read_text(encoding="utf-8-sig")):
        path = project_path(item["file"])
        if sha256(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
            raise ValueError(f"Public raw input fails source manifest check: {relative(path)}")
    return split, evaluation, scores, thresholds, inputs, result


def grouped_errors(
    evaluation: pd.DataFrame,
    scores: dict,
    thresholds: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Keep specimen outcomes alongside diagnosis and assay-group summaries."""
    y = binary_labels(evaluation.histology).to_numpy()
    cases = evaluation.copy()
    cases["y"] = y
    subtype = []
    grouped = []
    for name, score in scores.items():
        predicted = score >= thresholds[name]
        cases[f"{name}_score"] = score
        cases[f"{name}_flag"] = predicted
        cases[f"{name}_outcome"] = np.select(
            [(y == 1) & ~predicted, (y == 0) & predicted, (y == 1) & predicted],
            ["missed_rejection", "false_flag", "correct_rejection"],
            default="correct_no_rejection",
        )

        for diagnosis, target in DIAGNOSES.items():
            mask = evaluation.histology.eq(diagnosis).to_numpy()
            n = int(mask.sum())
            errors = int(np.sum(predicted[mask] != target))
            lower, upper = wilson(errors, n)
            subtype.append(
                {
                    "model": name,
                    "histology": diagnosis,
                    "error_type": "missed_rejection" if target else "false_flag",
                    "errors": errors,
                    "n": n,
                    "error_rate": ratio(errors, n),
                    "wilson_lower": lower,
                    "wilson_upper": upper,
                }
            )

        for field in METADATA:
            for value, group in evaluation.groupby(field, sort=True, dropna=False):
                mask = evaluation.index.isin(group.index)
                row = metrics(y[mask], score[mask], thresholds[name])
                diagnosis_counts = {
                    diagnosis: int(group.histology.eq(diagnosis).sum()) for diagnosis in DIAGNOSES
                }
                miss_lower, miss_upper = wilson(row["fn"], row["positives"])
                flag_lower, flag_upper = wilson(row["fp"], row["negatives"])
                grouped.append(
                    {
                        "model": name,
                        "field": field,
                        "group": value,
                        **row,
                        **diagnosis_counts,
                        "miss_rate": ratio(row["fn"], row["positives"]),
                        "false_flag_rate": ratio(row["fp"], row["negatives"]),
                        "miss_wilson_lower": miss_lower,
                        "miss_wilson_upper": miss_upper,
                        "false_flag_wilson_lower": flag_lower,
                        "false_flag_wilson_upper": flag_upper,
                    }
                )
    return cases, pd.DataFrame(subtype), pd.DataFrame(grouped)


def error_overlap(cases: pd.DataFrame, model_names: list[str]) -> pd.DataFrame:
    rows = []
    for i, first in enumerate(model_names):
        for second in model_names[i + 1 :]:
            for error, target in [("missed_rejection", 1), ("false_flag", 0)]:
                eligible = cases.y == target
                first_wrong = cases[f"{first}_outcome"] == error
                second_wrong = cases[f"{second}_outcome"] == error
                rows.append(
                    {
                        "model_a": first,
                        "model_b": second,
                        "error_type": error,
                        "eligible_n": int(eligible.sum()),
                        "both_error": int((first_wrong & second_wrong).sum()),
                        "a_only_error": int((first_wrong & ~second_wrong).sum()),
                        "b_only_error": int((~first_wrong & second_wrong).sum()),
                        "neither_error": int((eligible & ~first_wrong & ~second_wrong).sum()),
                    }
                )
    return pd.DataFrame(rows)


def composition(split: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cohort, group in split.groupby("split", sort=False):
        for field in ["histology", *METADATA]:
            for value, count in group[field].value_counts().items():
                rows.append(
                    {
                        "split": cohort,
                        "field": field,
                        "group": value,
                        "n": int(count),
                        "split_n": len(group),
                        "fraction": count / len(group),
                    }
                )
    return pd.DataFrame(rows)


def label(name: str) -> str:
    labels = {
        "logistic_all": "Multivariable logistic",
        "single_gene_IFNG": "IFNG",
        "training_prevalence": "Training constant",
    }
    if name.startswith("catboost"):
        return "CatBoost"
    return labels.get(name, name)


def savefig(fig, out: Path, name: str) -> None:
    for extension in ["svg", "png"]:
        fig.savefig(
            out / f"{name}.{extension}",
            dpi=180,
            bbox_inches="tight",
            facecolor="white",
            metadata={"Date": None} if extension == "svg" else None,
        )
    plt.close(fig)


def plots(
    out: Path,
    evaluation: pd.DataFrame,
    scores: dict,
    thresholds: dict,
    point: dict,
    subtype: pd.DataFrame,
    reliability_table: pd.DataFrame,
) -> None:
    """Apply shared style, then draw the six figures in report order."""
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.fonttype": "none",
            "svg.hashsalt": "kidney-analysis-20260915",
        }
    )
    y = binary_labels(evaluation.histology).to_numpy()
    model_names = list(scores)
    colors = dict(zip(scores, COLORS))

    plot_ranking_curves(out, y, scores, point, colors)
    plot_confusion_matrices(out, len(y), point, thresholds)
    plot_error_counts(out, y, model_names, point)
    plot_errors_by_diagnosis(out, model_names, subtype, colors)
    plot_score_distributions(out, y, scores, thresholds)
    plot_score_reliability(out, y.mean(), model_names, point, reliability_table, colors)


def plot_ranking_curves(
    out: Path,
    y: np.ndarray,
    scores: dict,
    point: dict,
    colors: dict,
) -> None:
    """Draw ROC and precision–recall curves, including frozen operating points."""
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.8), layout="constrained")
    roc_axis, precision_axis = axes
    for name, score in scores.items():
        fpr, tpr, _ = roc_curve(y, score)
        precision, recall, _ = precision_recall_curve(y, score)
        roc_axis.plot(
            fpr,
            tpr,
            color=colors[name],
            label=f"{label(name)}: AUC {point[name]['roc_auc']:.3f}",
        )
        if name != "training_prevalence":
            precision_axis.step(
                recall,
                precision,
                where="post",
                color=colors[name],
                label=f"{label(name)}: AP {point[name]['average_precision']:.3f}",
            )
        roc_axis.scatter(
            1 - point[name]["specificity"],
            point[name]["sensitivity"],
            color=colors[name],
            s=30,
            zorder=3,
        )
    precision_axis.axhline(
        y.mean(),
        color=COLORS[3],
        linestyle="--",
        label=f"Constant / prevalence: {y.mean():.1%}",
    )
    roc_axis.set(
        xlabel="False-positive rate (1 − specificity)",
        ylabel="Sensitivity",
        title="ROC: ranking rejection above no rejection",
    )
    precision_axis.set(
        xlabel="Recall (sensitivity)",
        ylabel="Precision",
        title="Precision–recall: AP is average precision",
    )
    for ax in axes:
        ax.set(xlim=(-0.02, 1.02), ylim=(-0.02, 1.03))
        ax.legend(loc="lower left", fontsize=8)
        ax.grid(alpha=0.15)
    fig.suptitle(
        f"Technical validation: {len(y)} specimens · {int(y.sum())} rejection · "
        f"{int((y == 0).sum())} no rejection\nROC dots mark discovery-selected thresholds",
        fontsize=13,
    )
    savefig(fig, out, "01_roc_precision_recall")


def plot_confusion_matrices(
    out: Path,
    specimen_count: int,
    point: dict,
    thresholds: dict,
) -> None:
    """Draw the four outcomes at each model's frozen threshold."""
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 8.1), layout="constrained")
    for ax, (name, row) in zip(axes.flat, point.items()):
        matrix = np.array([[row["tn"], row["fp"]], [row["fn"], row["tp"]]])
        ax.imshow(matrix, cmap="Blues", vmin=0, vmax=specimen_count / 2)
        words = [
            ["Correct no rejection", "False flags"],
            ["Missed rejection", "Correct rejection"],
        ]
        for i in range(2):
            for j in range(2):
                ax.text(
                    j,
                    i,
                    f"{matrix[i, j]}\n{words[i][j]}",
                    ha="center",
                    va="center",
                    color="white" if matrix[i, j] > specimen_count / 3 else "#152536",
                    fontsize=11,
                )
        ax.set(
            xticks=[0, 1],
            xticklabels=["No flag", "Flag"],
            yticks=[0, 1],
            yticklabels=["No rejection", "Rejection"],
            xlabel="Model decision",
            ylabel="Recorded diagnosis",
            title=f"{label(name)} · threshold {thresholds[name]:.4f}",
        )
    fig.suptitle("What each fixed threshold got right and wrong", fontsize=14)
    savefig(fig, out, "02_confusion_matrices")


def plot_error_counts(
    out: Path,
    y: np.ndarray,
    model_names: list[str],
    point: dict,
) -> None:
    """Compare missed rejection and false-flag counts at the frozen thresholds."""
    fig, ax = plt.subplots(figsize=(9.6, 4.2), layout="constrained")
    positions = np.arange(len(model_names))
    misses = [point[name]["fn"] for name in model_names]
    flags = [point[name]["fp"] for name in model_names]
    bars = ax.barh(
        positions - 0.18,
        misses,
        0.34,
        label=f"Missed rejection (of {int(y.sum())})",
        color="#B44F3F",
    )
    ax.bar_label(bars, padding=3)
    bars = ax.barh(
        positions + 0.18,
        flags,
        0.34,
        label=f"False flags (of {int((y == 0).sum())})",
        color="#176D8A",
    )
    ax.bar_label(bars, padding=3)
    ax.set(
        yticks=positions,
        yticklabels=[label(name) for name in model_names],
        xlabel="Specimens",
        xlim=(0, max(flags + misses) * 1.15),
        title="Error counts show the threshold tradeoff",
    )
    ax.invert_yaxis()
    ax.legend(loc="upper right")
    savefig(fig, out, "03_absolute_errors")


def plot_errors_by_diagnosis(
    out: Path,
    model_names: list[str],
    subtype: pd.DataFrame,
    colors: dict,
) -> None:
    """Draw error rates within each recorded diagnosis, with Wilson intervals."""
    fig, axes = plt.subplots(1, 4, figsize=(13, 4.9), sharey=True, layout="constrained")
    short_model_names = []
    for name in model_names:
        short_name = label(name).replace("Multivariable ", "").replace("Training ", "")
        short_model_names.append(short_name)
    for ax, diagnosis, title in zip(axes, DIAGNOSES, SHORT_DIAGNOSES):
        rows = subtype.loc[subtype.histology == diagnosis].set_index("model").loc[model_names]
        for i, (name, row) in enumerate(rows.iterrows()):
            error_bars = [
                [max(0, row.error_rate - row.wilson_lower)],
                [max(0, row.wilson_upper - row.error_rate)],
            ]
            ax.errorbar(
                i,
                row.error_rate,
                yerr=error_bars,
                fmt="o",
                color=colors[name],
                capsize=4,
                markersize=7,
            )
            ax.annotate(
                f"{int(row.errors)}/{int(row.n)}",
                (i, row.wilson_upper),
                xytext=(0, 7),
                textcoords="offset points",
                ha="center",
                fontsize=9,
            )
        ax.set(
            xticks=range(len(model_names)),
            xticklabels=short_model_names,
            title=title,
            ylim=(-0.035, 1.17),
        )
        ax.tick_params(axis="x", rotation=55)
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.grid(axis="y", alpha=0.15)
    axes[0].set_ylabel("Error rate within recorded diagnosis")
    fig.suptitle(
        "Errors by original diagnosis · counts / diagnosis total · 95% Wilson intervals",
        fontsize=13,
    )
    savefig(fig, out, "04_errors_by_diagnosis")


def plot_score_distributions(
    out: Path,
    y: np.ndarray,
    scores: dict,
    thresholds: dict,
) -> None:
    """Draw score distributions by recorded diagnosis, with frozen thresholds."""
    fig, axes = plt.subplots(2, 2, figsize=(10.6, 7.3), layout="constrained")
    for ax, (name, score) in zip(axes.flat, scores.items()):
        ax.hist(
            [score[y == 0], score[y == 1]],
            bins=np.linspace(0, 1, 21),
            histtype="step",
            linewidth=2,
            color=["#176D8A", "#B44F3F"],
            label=[f"No rejection (n={int((y == 0).sum())})", f"Rejection (n={int(y.sum())})"],
        )
        ax.axvline(
            thresholds[name],
            color="#202A34",
            linestyle="--",
            linewidth=1.3,
            label=f"Threshold {thresholds[name]:.4f}",
        )
        ax.set(
            xlabel="Model score",
            ylabel="Specimens per 0.05 score bin",
            title=label(name),
            xlim=(0, 1),
        )
        ax.legend(fontsize=8)
    fig.suptitle("Score distributions and frozen thresholds", fontsize=14)
    savefig(fig, out, "05_score_distributions")


def plot_score_reliability(
    out: Path,
    prevalence: float,
    model_names: list[str],
    point: dict,
    reliability_table: pd.DataFrame,
    colors: dict,
) -> None:
    """Compare mean scores with observed fractions in the fixed score bins."""
    fig, axes = plt.subplots(2, 2, figsize=(10.6, 9.2), layout="constrained")
    for ax, name in zip(axes.flat, model_names):
        rows = reliability_table.loc[(reliability_table.model == name) & (reliability_table.n > 0)]
        ax.plot([0, 1], [0, 1], color="#8B939B", linestyle="--", linewidth=1)
        observed = rows.observed_fraction.to_numpy()
        error_bars = [
            np.maximum(0, observed - rows.wilson_lower),
            np.maximum(0, rows.wilson_upper - observed),
        ]
        ax.errorbar(
            rows.mean_score,
            observed,
            yerr=error_bars,
            fmt="o-",
            color=colors[name],
            capsize=3,
            linewidth=1,
        )
        for row in rows.itertuples():
            # Counts are at fixed bin centers, independent of observed fraction.
            bin_center = (row.lower_edge + row.upper_edge) / 2
            ax.text(bin_center, -0.1, str(row.n), ha="center", va="center", fontsize=8)
        ax.text(-0.02, -0.1, "n", ha="right", va="center", fontsize=9)
        ax.set(
            xlim=(-0.02, 1.02),
            ylim=(-0.16, 1.05),
            xlabel="Mean score in bin (counts below axis)",
            ylabel="Observed rejection fraction",
            title=(
                f"{label(name)} · Brier {point[name]['brier']:.3f}\n"
                f"Mean score {point[name]['mean_score']:.1%} · observed {prevalence:.1%}"
            ),
        )
        ax.set_yticks(np.linspace(0, 1, 6))
        ax.grid(alpha=0.13)
    fig.suptitle(
        "Do scores match observed fractions?\n"
        "Ten fixed bins of width 0.1; 95% Wilson bars; empty bins omitted",
        fontsize=13,
    )
    savefig(fig, out, "06_score_reliability")


def clean_json(value):
    if isinstance(value, dict):
        return {key: clean_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clean_json(item) for item in value]
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def write_json(path: Path, value) -> None:
    path.write_text(
        json.dumps(clean_json(value), indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def percent(value: float) -> str:
    return f"{value:.1%}" if np.isfinite(value) else "Undefined"


def report(
    out: Path,
    run: Path,
    case_dir: Path,
    split: pd.DataFrame,
    point: dict,
    intervals: pd.DataFrame,
    differences: pd.DataFrame,
    subtype: pd.DataFrame,
    grouped: pd.DataFrame,
    overlap: pd.DataFrame,
    bins: pd.DataFrame,
    n_bootstrap: int,
    seed: int,
    result: dict,
) -> None:
    """Assemble the written interpretation and tables in their reading order."""
    selected = next(iter(point))
    selected_row = point[selected]
    logistic = point["logistic_all"]
    ifng = point["single_gene_IFNG"]
    metric_intervals = intervals.set_index(["model", "metric"])
    study_review_link = Path(
        os.path.relpath(ROOT / "docs/references/STUDY_AUDIT_20260919.md", start=out)
    ).as_posix()

    def interval(name, metric, percentage=True):
        row = metric_intervals.loc[(name, metric)]
        if not np.isfinite(row.estimate):
            return "Undefined"
        values = [row.estimate, row.lower, row.upper]
        if percentage:
            estimate, lower, upper = [f"{100 * value:.1f}%" for value in values]
        else:
            estimate, lower, upper = [f"{value:.3f}" for value in values]
        return f"{estimate} ({lower}–{upper})"

    def add_table_row(*cells: str) -> None:
        lines.append("| " + " | ".join(cells) + " |")

    lines = [
        "# Finished analysis of the frozen primary classifier",
        "",
        f"Source run: `{relative(run)}`. Analysis seed: {seed}. Target: any recorded rejection in an "
        f"already collected biopsy.",
        "",
        "## Main finding",
        "",
        (
            f"On {selected_row['n']} author technical-validation specimens, {label(selected)} missed "
            f"{selected_row['fn']} of {selected_row['positives']} rejection cases and falsely flagged "
            f"{selected_row['fp']} of {selected_row['negatives']} no-rejection cases. "
            f"Logistic regression missed {logistic['fn']} with {logistic['fp']} false flags; IFNG "
            f"missed {ifng['fn']} with {ifng['fp']} false flags. "
            f"At these frozen thresholds, {label(selected)} detected "
            f"{logistic['fn'] - selected_row['fn']} more rejection cases than logistic regression. "
            f"Compared with IFNG, it produced {ifng['fp'] - selected_row['fp']} fewer false flags and "
            f"{selected_row['fn'] - ifng['fn']} more misses."
        ),
        "",
        "| Model | Threshold | Misses / rejection | False flags / no rejection | Sensitivity (95% "
        "interval) | Specificity (95% interval) |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for name, row in point.items():
        add_table_row(
            label(name),
            f"{row['threshold']:.6f}",
            f"{row['fn']} / {row['positives']}",
            f"{row['fp']} / {row['negatives']}",
            interval(name, "sensitivity"),
            interval(name, "specificity"),
        )
    lines += [
        "",
        "| Model | ROC-AUC (95% interval) | Average precision | Precision | Negative predictive value "
        "| Accuracy |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for name, row in point.items():
        add_table_row(
            label(name),
            interval(name, "roc_auc", False),
            f"{row['average_precision']:.3f}",
            percent(row["ppv"]),
            percent(row["npv"]),
            percent(row["accuracy"]),
        )
    lines += [
        "",
        (
            "The constant score is the training rejection fraction, evaluated at 0.5. It flags every "
            "validation specimen because training prevalence exceeds 0.5. "
            "Its negative predictive value is undefined: it makes no negative predictions. The "
            "preserved original run used a zero-denominator fallback of zero; this analysis corrects "
            "that display without altering the run."
        ),
        "",
        (
            f"The selected threshold reached {result['screen']['sensitivity']:.1%} sensitivity on "
            f"screening data; validation sensitivity was {selected_row['sensitivity']:.1%}, below the "
            f"experimental 90% target. "
            "Threshold selection and probability calibration are separate: a threshold picks a "
            "flagging rule; calibration asks whether scores correspond to observed fractions."
        ),
        "",
        "## Paired comparison and uncertainty",
        "",
        (
            f"Intervals use {n_bootstrap:,} ordinary bootstrap resamples of {selected_row['n']} biopsy "
            f"specimens with replacement, seed {seed}, and the 2.5th and 97.5th percentiles. "
            "Each resample uses the same specimen positions for every model. Models, preprocessing, "
            "and thresholds remain fixed. These intervals describe evaluation-sample uncertainty, "
            "not uncertainty from model fitting, feature selection, or threshold selection. Patient "
            "and center independence are unverified; repeated or related specimens could make these "
            "intervals too narrow. "
            "Small subgroup intervals are descriptive, with no multiplicity adjustment."
        ),
        "",
        (
            f"Differences below are **{label(selected)} minus the comparison model**. Negative "
            f"miss/false-flag counts and Brier differences favor the selected model; positive "
            f"sensitivity/specificity/AUC differences favor it. "
            "Count intervals describe differences in a same-size resampled cohort, not a forecast for "
            "a new clinic."
        ),
        "",
        "| Comparison | Metric | Difference | 95% paired interval |",
        "| --- | --- | ---: | --- |",
    ]
    for row in differences.itertuples():
        if row.metric in ["sensitivity", "specificity"]:
            estimate = f"{row.estimate * 100:+.2f} pp"
            limits = f"{row.lower * 100:+.2f} to {row.upper * 100:+.2f} pp"
        elif row.metric in ["fn", "fp"]:
            estimate = f"{row.estimate:+.0f}"
            limits = f"{row.lower:+.2f} to {row.upper:+.2f}"
        else:
            estimate = f"{row.estimate:+.4f}"
            limits = f"{row.lower:+.4f} to {row.upper:+.4f}"
        metric_label = {
            "fn": "Missed rejection",
            "fp": "False flags",
            "roc_auc": "ROC-AUC",
            "brier": "Brier score",
        }.get(row.metric, row.metric.capitalize())
        add_table_row(label(row.minus_model), metric_label, estimate, limits)

    auc_difference = differences.loc[
        (differences.minus_model == "logistic_all") & (differences.metric == "roc_auc")
    ].iloc[0]
    if auc_difference.lower <= 0 <= auc_difference.upper:
        auc_interpretation = (
            "The ROC-AUC difference interval includes zero, so a clear ranking advantage "
            "over logistic regression is not established by this sample."
        )
    else:
        auc_interpretation = (
            "The ROC-AUC difference interval only just excludes zero under this fixed-model "
            "specimen-resampling calculation; its lower endpoint is about 0.0001. "
            "The sensitivity, miss-count, specificity, and Brier-difference intervals include zero. "
            "The practical advantage over logistic regression remains uncertain, "
            "and these intervals do not measure training or selection uncertainty."
        )
    lines += [
        "",
        (
            "The point estimates favor CatBoost over logistic regression in this cohort, but the "
            "paired intervals show how much the comparison can vary. " + auc_interpretation
        ),
        "",
        "## Missed rejection and false flags",
        "",
        "These are errors against recorded histological labels, without chart review or adjudication. "
        "They do not establish which diagnosis is biologically correct.",
        "",
        "| Original diagnosis | CatBoost errors / specimens | Logistic errors / specimens | IFNG "
        "errors / specimens | Error counted |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for diagnosis in DIAGNOSES:
        rows = subtype.loc[subtype.histology == diagnosis].set_index("model")
        counts = [
            f"{int(rows.loc[name, 'errors'])} / {int(rows.loc[name, 'n'])}"
            for name in [selected, "logistic_all", "single_gene_IFNG"]
        ]
        error_type = "False flag" if diagnosis == "No Rejection" else "Missed rejection"
        add_table_row(diagnosis, *counts, error_type)
    lines += [
        "",
        "The diagnosis plot and CSV show each denominator and 95% Wilson intervals. The subtype "
        "analysis evaluates the binary classifier; it is not a separate subtype-prediction task.",
        "",
        "| Comparison with CatBoost | Error type | Both models wrong | CatBoost only wrong | "
        "Comparison only wrong |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    selected_overlap = overlap.loc[
        (overlap.model_a == selected) & (overlap.model_b != "training_prevalence")
    ]
    for row in selected_overlap.itertuples():
        add_table_row(
            label(row.model_b),
            row.error_type.replace("_", " "),
            str(row.both_error),
            str(row.a_only_error),
            str(row.b_only_error),
        )
    lines += [
        "",
        (
            f"The local specimen review is `{relative(case_dir)}/specimen_review.csv`; "
            f"`selected_model_errors.csv` contains only the selected model's errors. "
            "They retain original diagnosis, assay date/cartridge/scanner, all model scores and "
            "decisions, and outcome categories. Per-specimen files are Git-ignored."
        ),
        "",
        "## Score reliability",
        "",
        (
            "The reliability plot uses ten fixed equal-width score bins: [0, 0.1), …, [0.9, 1]. Each "
            "point uses the actual mean score and observed rejection fraction within its bin. "
            "Counts and 95% Wilson intervals make sparse bins visible; empty bins have no point. Brier "
            "score is mean squared score error, so lower is better; it reflects both discrimination "
            "and calibration. "
            "A lower Brier score alone does not establish better calibration. Method reference: "
            "[scikit-learn probability calibration "
            "documentation](https://scikit-learn.org/stable/modules/calibration.html), accessed "
            "September 15, 2026."
        ),
        "",
        "| Model | Mean score | Observed rejection | Mean minus observed | Brier score (95% interval) |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for name, row in point.items():
        add_table_row(
            label(name),
            f"{row['mean_score']:.1%}",
            f"{row['prevalence']:.1%}",
            f"{(row['mean_score'] - row['prevalence']) * 100:+.1f} pp",
            interval(name, "brier", False),
        )
    substantial = bins.loc[(bins.model == selected) & (bins.n >= 10)].copy()
    substantial["gap"] = abs(substantial.mean_score - substantial.observed_fraction)
    example = substantial.sort_values("gap", ascending=False).iloc[0]
    high = bins.loc[(bins.model == selected) & (bins.bin == 10)].iloc[0]
    lines += [
        "",
        (
            f"The selected model's average score differs from the observed fraction by "
            f"{(selected_row['mean_score'] - selected_row['prevalence']) * 100:+.1f} percentage points. "
            f"Among its bins with at least 10 specimens, the largest score-versus-observation gap is "
            f"in [{example.lower_edge:.1f}, "
            f"{example.upper_edge:.1f}{']' if example.upper_edge == 1 else ')'}: "
            f"mean score {example.mean_score:.1%}, but {int(example.positives)}/{int(example.n)} "
            f"({example.observed_fraction:.1%}) had recorded rejection "
            f"(95% Wilson interval {example.wilson_lower:.1%}–{example.wilson_upper:.1%}). This is a "
            f"descriptive example selected after inspecting the fixed bins. "
            f"In the [0.9, 1.0] bin, mean score was {high.mean_score:.1%} and "
            f"{int(high.positives)}/{int(high.n)} ({high.observed_fraction:.1%}) had rejection "
            f"(95% Wilson interval {high.wilson_lower:.1%}–{high.wilson_upper:.1%}). "
            "Good ranking does not by itself make each score a reliable probability, and agreement of "
            "averages does not establish calibration in each score range. "
            "Several bins contain few specimens. Continue calling the output a **model score**; no "
            "recalibration was fitted on validation data. Any future calibration fit must use "
            "discovery data and be evaluated as a separate follow-up analysis."
        ),
        "",
        "## Assay metadata and study composition",
        "",
        (
            "Metadata grouping uses deposited assay Date, CartridgeID, and ScannerID. These fields "
            "describe processing; they are not patient or center IDs and are excluded from model "
            "predictors. "
            "Every group table includes rejection and no-rejection denominators, original diagnosis "
            "counts, misses, false flags, and Wilson intervals for the two error rates."
        ),
        "",
        "| Split | Specimens | Rejection fraction | No rejection | Antibody-mediated | T cell-mediated "
        "| Mixed |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for cohort in SPLITS:
        group = split.loc[split.split == cohort]
        counts = [str(int(group.histology.eq(diagnosis).sum())) for diagnosis in DIAGNOSES]
        add_table_row(
            cohort, str(len(group)), f"{binary_labels(group.histology).mean():.1%}", *counts
        )
    lines += [
        "",
        "| Metadata field | Discovery groups | Validation groups | Groups shared across cohorts |",
        "| --- | ---: | ---: | ---: |",
    ]
    for field in METADATA:
        discovery = set(split.loc[split.split != "author_validation", field])
        validation = set(split.loc[split.split == "author_validation", field])
        add_table_row(
            field, str(len(discovery)), str(len(validation)), str(len(discovery & validation))
        )
    lines += [
        "",
        "| Validation scanner | Specimens | Rejection | Misses / rejection | False flags / no rejection |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    selected_groups = grouped.loc[grouped.model == selected]
    for row in selected_groups.loc[selected_groups.field == "ScannerID"].itertuples():
        add_table_row(
            str(row.group),
            str(row.n),
            f"{row.prevalence:.1%}",
            f"{row.fn} / {row.positives}",
            f"{row.fp} / {row.negatives}",
        )
    lines += [
        "",
        "| Validation assay date | Specimens | Rejection fraction | Misses / rejection | False flags / "
        "no rejection |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in selected_groups.loc[selected_groups.field == "Date"].itertuples():
        add_table_row(
            str(row.group),
            str(row.n),
            f"{row.prevalence:.1%}",
            f"{row.fn} / {row.positives}",
            f"{row.fp} / {row.negatives}",
        )
    lines += [
        "",
        (
            "Discovery and validation used different dates and cartridges, but the same scanner. Those "
            "assay groups are therefore tied to cohort membership; they cannot separate cohort effects "
            "from assay effects. "
            "Assay-group error rates must be read alongside diagnosis composition and small "
            "denominators. The recorded groups do not isolate a scanner, cartridge, or date effect "
            "from specimen mix. "
            "These are descriptive checks, not evidence of a causal batch effect or verified "
            "transportability to new centers."
        ),
        "",
        "Viral assay-target interpretation is documented separately in [viral-target "
        "review](../20260915_viral/REPORT.md).",
        "",
        "## Reproduce and inspect",
        "",
        "```powershell",
        "uv run python scripts/analyze_results.py --output-dir "
        "results/analysis/20260915_baseline_check --case-dir "
        "data/processed/analysis/20260915_baseline_check",
        "```",
        "",
        (
            "This command reads saved predictions and cohort assignments, checks exact specimen sets "
            "and diagnosis mappings, verifies frozen flags and original aggregate results, "
            "then recomputes all summaries without fitting or changing thresholds. Saved inputs are "
            "verified against the completed-run manifest, and physical raw files against its "
            "public-source manifest. "
            "Inputs, hashes, settings, package versions, and output hashes are recorded in "
            "`analysis_manifest.json`. "
            "The original baseline outputs are preserved. Completed analysis and specimen-output "
            "directories are never overwritten; choose fresh directory names for each rerun. "
            "Additional reports may use `--run-dir`, `--output-dir`, and `--case-dir` with new "
            "project-relative directories."
        ),
        "",
        "### Main charts",
        "",
        "Each PNG has an editable SVG with text retained as text and a corresponding aggregate CSV "
        "where applicable.",
        "",
        "1. [ROC and precision–recall](figures/01_roc_precision_recall.svg)",
        "2. [Confusion matrices](figures/02_confusion_matrices.svg)",
        "3. [Absolute error counts](figures/03_absolute_errors.svg)",
        "4. [Errors by diagnosis](figures/04_errors_by_diagnosis.svg)",
        "5. [Score distributions](figures/05_score_distributions.svg)",
        "6. [Score reliability](figures/06_score_reliability.svg)",
        "",
        (
            "Aggregate tables: `model_metrics.csv`, `metric_intervals.csv`, `paired_differences.csv`, "
            "`errors_by_diagnosis.csv`, `error_overlap.csv`, "
            "`reliability_bins.csv`, `assay_group_errors.csv`, and `cohort_composition.csv`. Full "
            "metric intervals include precision, negative predictive value, average precision, "
            "accuracy, Brier score, and error counts."
        ),
        "",
        "## Scope of the evidence",
        "",
        (
            "The original source study included 1,193 transplant biopsies and 202 native-kidney "
            "controls. Its 345-specimen technical-validation cohort included 334 transplant "
            "biopsies and 11 native-kidney controls. These published totals describe the source "
            "cohorts; the public metadata do not identify individual native-kidney specimens. "
            f"See the [September 19, 2026 source review]({study_review_link})."
        ),
        "",
        (
            "The data establish agreement with recorded rejection diagnoses in this deposited study. "
            "Technical validation is the authors' held-out cohort, not a prospective clinical trial. "
            "The study does not establish future rejection prediction, care benefit, clinical "
            "deployment, or patient/center independence. This analysis completes reporting of the "
            "existing fixed run; "
            "no new model, threshold, or calibrated model was selected from its validation results."
        ),
        "",
    ]
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def analyze_run(run: Path, out: Path, case_dir: Path, n_bootstrap: int, seed: int) -> None:
    """Verify a saved run, summarize its predictions, and write the evidence."""
    if out == run or run in out.parents or out in run.parents:
        raise ValueError("Analysis output must be separate from the preserved training run")
    if not case_dir.is_relative_to(ROOT / "data" / "processed"):
        raise ValueError("Per-specimen tables must be under ignored data/processed")
    for destination in [out, case_dir]:
        if destination.exists():
            raise ValueError(
                f"Output destination already exists; choose a new directory: {relative(destination)}"
            )

    split, evaluation, scores, thresholds, inputs, result = load_run(run)
    configuration = {
        "run_dir": relative(run),
        "output_dir": relative(out),
        "case_dir": relative(case_dir),
        "bootstrap_replicates": n_bootstrap,
        "seed": seed,
        "bootstrap_unit": "biopsy specimen",
        "bootstrap_scheme": "ordinary paired nonparametric percentile",
        "models_and_thresholds": thresholds,
        "reliability_edges": np.linspace(0, 1, 11).tolist(),
    }
    input_records = [{"file": relative(path), "sha256": sha256(path)} for path in inputs]
    out.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    figures = out / "figures"
    figures.mkdir(exist_ok=True)

    # Calculate summaries from the same fixed predictions and thresholds.
    y = binary_labels(evaluation.histology).to_numpy()
    point, intervals, differences = paired_bootstrap(y, scores, thresholds, n_bootstrap, seed)
    cases, subtype, grouped = grouped_errors(evaluation, scores, thresholds)
    overlap = error_overlap(cases, list(scores))
    reliability_rows = []
    for name, score in scores.items():
        reliability_rows.extend(reliability(y, score, name))
    bins = pd.DataFrame(reliability_rows)
    model_metrics = pd.DataFrame.from_dict(point, orient="index").rename_axis("model").reset_index()
    tables = {
        "model_metrics": model_metrics,
        "metric_intervals": intervals,
        "paired_differences": differences,
        "errors_by_diagnosis": subtype,
        "assay_group_errors": grouped,
        "error_overlap": overlap,
        "reliability_bins": bins,
        "cohort_composition": composition(split),
    }

    # Keep aggregate tables with the report and specimen details in ignored data.
    for name, frame in tables.items():
        frame.to_csv(out / f"{name}.csv", index=False)
    write_json(out / "model_metrics.json", point)
    cases.to_csv(case_dir / "specimen_review.csv", index_label="sample")
    selected = next(iter(scores))
    is_error = cases[f"{selected}_outcome"].isin(["missed_rejection", "false_flag"])
    selected_errors = cases.loc[is_error].sort_values(f"{selected}_score")
    selected_errors.to_csv(case_dir / "selected_model_errors.csv", index_label="sample")
    plots(figures, evaluation, scores, thresholds, point, subtype, bins)
    report(
        out,
        run,
        case_dir,
        split,
        point,
        intervals,
        differences,
        subtype,
        grouped,
        overlap,
        bins,
        n_bootstrap,
        seed,
        result,
    )

    # Write the manifest last, after every output is complete.
    outputs = [out / "REPORT.md", out / "model_metrics.json"]
    outputs.extend(out / f"{name}.csv" for name in tables)
    outputs.extend(sorted(figures.glob("*")))
    outputs.extend([case_dir / "specimen_review.csv", case_dir / "selected_model_errors.csv"])
    write_analysis_manifest(out, run, configuration, input_records, outputs, selected)
    print(f"Analysis complete: {relative(out / 'REPORT.md')}")
    print(
        f"{len(evaluation)} matched specimens; {n_bootstrap} paired bootstrap replicates; {len(scores)} fixed models"
    )


def write_analysis_manifest(
    out: Path,
    run: Path,
    configuration: dict,
    input_records: list[dict],
    outputs: list[Path],
    selected: str,
) -> None:
    source_paths = [
        Path(__file__),
        ROOT / "src/kidney_biopsy/preprocessing.py",
        ROOT / "src/kidney_biopsy/prediction.py",
    ]
    dependencies = ["numpy", "pandas", "scikit-learn", "matplotlib"]
    manifest = {
        "configuration": configuration,
        "inputs": input_records,
        "source": {"file": relative(Path(__file__)), "sha256": sha256(Path(__file__))},
        "source_code": [{"file": relative(path), "sha256": sha256(path)} for path in source_paths],
        "environment_lock": {"file": "uv.lock", "sha256": sha256(ROOT / "uv.lock")},
        "python": platform.python_version(),
        "dependencies": {name: importlib.metadata.version(name) for name in dependencies},
        "model_version": f"{relative(run)}:{selected}",
        "provenance_checks": {
            "saved_inputs_match_run_manifest": True,
            "public_manifest_matches_run": True,
            "physical_raw_files_match_source_manifest": True,
        },
        "run_manifest_sha256": sha256(run / "run_manifest.json"),
        "outputs": [
            {"file": relative(path), "sha256": sha256(path), "bytes": path.stat().st_size}
            for path in outputs
        ],
    }
    write_json(out / "analysis_manifest.json", manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default="results/reproduction/baseline")
    parser.add_argument("--output-dir", default="results/analysis/20260915_baseline")
    parser.add_argument("--case-dir", default="data/processed/analysis/20260915_baseline")
    parser.add_argument("--bootstrap", type=int, default=BOOTSTRAPS)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    run = project_path(args.run_dir)
    out = project_path(args.output_dir)
    case_dir = project_path(args.case_dir)
    analyze_run(run, out, case_dir, args.bootstrap, args.seed)


if __name__ == "__main__":
    main()
