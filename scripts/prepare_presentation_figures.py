"""Make large, editable presentation figures from verified saved aggregate results.

This does not fit a model, change a threshold, or recompute evaluation results.
Run from the project root and choose a new output directory for each completed set.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

from kidney_biopsy.prediction import project_path, sha256, verify_artifact

MODELS = ("catboost_all_depth4", "logistic_all", "single_gene_IFNG")
LABELS = ("CatBoost", "Logistic regression", "IFNG alone")
INK = "#243746"
BLUE = "#146c86"
RUST = "#b24d3d"
ANALYSIS_DIR = "results/analysis/20260915_baseline"


def new_figure(title: str, subtitle: str) -> Figure:
    figure = Figure(figsize=(16, 9), facecolor="white")
    FigureCanvasAgg(figure)
    figure.text(0.045, 0.945, title, fontsize=28, weight="bold", color=INK)
    figure.text(0.045, 0.885, subtitle, fontsize=19, color=INK)
    return figure


def save_figure(figure: Figure, output: Path, name: str) -> None:
    figure.savefig(output / f"{name}.svg", metadata={"Date": None})
    figure.savefig(output / f"{name}.png", dpi=150)


def error_counts(metrics: pd.DataFrame) -> Figure:
    selected = metrics.loc[list(MODELS)]
    total = int(selected.iloc[0]["n"])
    rejection = int(selected.iloc[0]["positives"])
    no_rejection = int(selected.iloc[0]["negatives"])
    figure = new_figure(
        "Compare the two kinds of error",
        f"{total} author technical-validation specimens; each model uses its frozen threshold",
    )
    positions = np.arange(len(MODELS))
    for panel, (field, denominator, title, color) in enumerate(
        (
            ("fn", rejection, "Missed rejection", RUST),
            ("fp", no_rejection, "False rejection flags", BLUE),
        )
    ):
        axis = figure.add_axes((0.265 + panel * 0.365, 0.265, 0.315, 0.50))
        counts = selected[field].to_numpy(dtype=int)
        axis.barh(positions, counts, height=0.48, color=color)
        axis.set_yticks(positions, LABELS if panel == 0 else [""] * len(MODELS))
        axis.invert_yaxis()
        axis.set_xlim(0, 90)
        axis.set_xticks((0, 25, 50, 75))
        axis.set_title(f"{title}\n(out of {denominator})", fontsize=22, loc="left", pad=22)
        axis.set_xlabel("Specimens", fontsize=18, labelpad=12)
        axis.tick_params(axis="y", length=0, labelsize=21, pad=18)
        axis.tick_params(axis="x", labelsize=18)
        for index, count in enumerate(counts):
            axis.text(count + 2, index, str(count), va="center", fontsize=25, color=INK)
        for side in ("top", "right", "left"):
            axis.spines[side].set_visible(False)
        axis.spines["bottom"].set_color("#aab5bd")
    constant = metrics.loc["training_prevalence"]
    figure.text(
        0.045,
        0.135,
        f"Constant baseline: {int(constant['fn'])} misses; "
        f"{int(constant['fp'])} false flags. It flagged every specimen.",
        fontsize=19,
        color=INK,
    )
    figure.text(
        0.045,
        0.075,
        "CatBoost's practical advantage over logistic regression remains uncertain.",
        fontsize=19,
        color=INK,
    )
    return figure


def score_reliability(metrics: pd.DataFrame, bins: pd.DataFrame) -> Figure:
    selected = bins.loc[bins["model"].eq(MODELS[0]) & bins["n"].gt(0)].copy()
    metric = metrics.loc[MODELS[0]]
    figure = new_figure(
        "Keep calling the output a model score",
        "CatBoost; author technical validation; ten fixed score bins; 95% Wilson intervals",
    )
    axis = figure.add_axes((0.09, 0.22, 0.47, 0.56))
    axis.plot((0, 1), (0, 1), color="#8b98a2", linestyle="--", linewidth=2)
    scores = selected["mean_score"].to_numpy()
    observed = selected["observed_fraction"].to_numpy()
    errors = np.vstack(
        (
            observed - selected["wilson_lower"].to_numpy(),
            selected["wilson_upper"].to_numpy() - observed,
        )
    )
    axis.errorbar(scores, observed, yerr=errors, fmt="o", color=BLUE, markersize=9, capsize=5)
    axis.set_xlim(-0.025, 1.025)
    axis.set_ylim(-0.10, 1.025)
    axis.set_xticks(np.linspace(0, 1, 6))
    axis.set_yticks(np.linspace(0, 1, 6))
    axis.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    axis.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    axis.set_xlabel("Mean model score in bin", fontsize=20, labelpad=15)
    axis.set_ylabel("Observed rejection fraction", fontsize=20, labelpad=15)
    axis.tick_params(labelsize=18)
    axis.grid(alpha=0.12)
    axis.spines[["top", "right"]].set_visible(False)
    for midpoint, count in zip(
        (selected["lower_edge"] + selected["upper_edge"]) / 2, selected["n"], strict=True
    ):
        axis.text(midpoint, -0.065, str(int(count)), ha="center", fontsize=14, color=INK)
    axis.text(-0.02, -0.065, "n", ha="right", fontsize=14, color=INK)
    example = selected.loc[selected["bin"].eq(9)].iloc[0]
    figure.text(0.625, 0.72, "One descriptive example", fontsize=22, weight="bold", color=INK)
    figure.text(
        0.625,
        0.57,
        f"Score range: {example['lower_edge']:.1f}–{example['upper_edge']:.1f}\n"
        f"Mean score: {example['mean_score']:.1%}",
        fontsize=22,
        linespacing=1.5,
        color=INK,
    )
    figure.text(
        0.625,
        0.415,
        f"Recorded rejection: {int(example['positives'])}/{int(example['n'])}\n"
        f"Observed fraction: {example['observed_fraction']:.1%}",
        fontsize=22,
        linespacing=1.5,
        color=INK,
    )
    figure.text(0.625, 0.275, f"Brier score: {metric['brier']:.3f}", fontsize=22, color=INK)
    figure.text(
        0.045,
        0.07,
        "Sparse bins leave uncertainty. No calibration model was fitted on these specimens.",
        fontsize=19,
        color=INK,
    )
    return figure


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="results/presentation/20260917_evidence")
    args = parser.parse_args()
    root = Path.cwd().resolve()
    analysis = project_path(root, ANALYSIS_DIR)
    output = project_path(root, args.output_dir)
    if output.exists():
        parser.error("Output directory already exists; choose a new --output-dir.")

    manifest_path = analysis / "analysis_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    recorded_outputs = {item["file"]: item for item in manifest["outputs"]}
    inputs = []
    for filename in ("model_metrics.csv", "reliability_bins.csv"):
        relative = (analysis / filename).relative_to(root).as_posix()
        if relative not in recorded_outputs:
            raise ValueError(f"Aggregate file is absent from the analysis manifest: {relative}")
        record = recorded_outputs[relative]
        verify_artifact(root, record)
        inputs.append(record)
    metrics = pd.read_csv(analysis / "model_metrics.csv").set_index("model")
    bins = pd.read_csv(analysis / "reliability_bins.csv")
    if not metrics.index.is_unique:
        raise ValueError("Aggregate metrics contain duplicate models.")
    if metrics.loc[list(MODELS), ["n", "positives", "negatives"]].nunique().max() != 1:
        raise ValueError("Model comparisons must use the same cohort counts.")

    output.mkdir(parents=True)
    with matplotlib.rc_context({"font.family": "DejaVu Sans", "svg.fonttype": "none"}):
        save_figure(error_counts(metrics), output, "01_model_errors")
        save_figure(score_reliability(metrics, bins), output, "02_score_reliability")
    captions = """# Figures for the interview presentation

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
"""
    (output / "README.md").write_text(captions, encoding="utf-8")
    record = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_dir": ANALYSIS_DIR,
        "source_model_version": manifest["model_version"],
        "analysis_manifest": {
            "file": manifest_path.relative_to(root).as_posix(),
            "sha256": sha256(manifest_path),
        },
        "inputs": inputs,
        "script": {
            "file": "scripts/prepare_presentation_figures.py",
            "sha256": sha256(root / "scripts/prepare_presentation_figures.py"),
        },
        "environment_lock_sha256": sha256(root / "uv.lock"),
        "matplotlib_version": matplotlib.__version__,
        "outputs": [
            {
                "file": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in sorted(output.iterdir())
        ],
    }
    (output / "manifest.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote verified presentation figures to {args.output_dir}")


if __name__ == "__main__":
    main()
