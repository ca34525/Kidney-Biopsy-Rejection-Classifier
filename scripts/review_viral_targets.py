"""Describe BK assay signals and study composition without changing the model.

Run from the project root: uv run python scripts/review_viral_targets.py
Aggregate records are tracked; specimen-level records stay under data/processed.
"""
from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

from kidney_biopsy import map_diagnoses, normalize_counts, read_geo_matrix, read_rcc_archive

if __package__:
    from .verify_local_data import local_path, records, sha256 as digest, verify
else:
    from verify_local_data import local_path, records, sha256 as digest, verify


ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["BK  large T Ag", "BK  VP1"]
DIAGNOSES = ["No Rejection", "Antibody-mediated Rejection", "T cell-mediated Rejection", "Mixed Rejection"]
COHORTS = {"Discovery cohort sample": "Discovery", "Validation cohort sample": "Author technical validation"}
SOURCES = [
    {"title": "GSE212160 study deposit", "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212160", "checked": "2026-09-15"},
    {"title": "Banff 2019 B-HOT panel consensus, Table 2", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7496585/", "checked": "2026-09-15"},
    {"title": "Zhang et al. Supplementary Table S3", "url": "https://ars.els-cdn.com/content/image/1-s2.0-S0023683723002477-mmc5.docx", "local_source": "data/reference/study/rejection_supplement_5.txt", "checked": "2026-09-15"},
    {"title": "Zhang et al. Supplementary Methods", "url": "https://ars.els-cdn.com/content/image/1-s2.0-S0023683723002477-mmc6.docx", "local_source": "data/reference/study/rejection_supplement_6.txt", "checked": "2026-09-15"},
]


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, float_format="%.8g")


def summaries(frame: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    rows = []
    for keys, values in frame.groupby(groups, observed=True, sort=True):
        if not isinstance(keys, tuple):
            keys = (keys,)
        for target in TARGETS:
            signal = values[target]
            rows.append({**dict(zip(groups, keys)), "target": target, "n": len(values),
                         "min": signal.min(), "p10": signal.quantile(.1),
                         "p25": signal.quantile(.25), "median": signal.median(),
                         "p75": signal.quantile(.75), "p90": signal.quantile(.9),
                         "max": signal.max(), "mean": signal.mean(),
                         "raw_count_median": values[f"{target} raw count"].median(),
                         "raw_count_max": values[f"{target} raw count"].max()})
    return pd.DataFrame(rows)


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
                     + ["| " + " | ".join(row) + " |" for row in rows])


def higher_signal_outcomes(frame: pd.DataFrame) -> dict[str, int]:
    """Count validation outcomes among specimens above the descriptive reference."""
    higher = frame.both_BK_signals_above_zero
    rejection = map_diagnoses(frame.diagnosis).astype(bool)
    predicted = frame.predicted.astype(bool)  # Joining discovery rows gives this column object dtype.
    return {
        "n": int(higher.sum()),
        "no_rejection": int((higher & ~rejection).sum()),
        "rejection": int((higher & rejection).sum()),
        "negative_results": int((higher & ~predicted).sum()),
        "false_flags": int((higher & ~rejection & predicted).sum()),
        "missed_rejection": int((higher & rejection & ~predicted).sum()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", default="results/reproduction/baseline")
    parser.add_argument("--output-dir", default="results/analysis/20260915_viral")
    parser.add_argument("--specimen-dir", default="data/processed/analysis/20260915_viral")
    args = parser.parse_args()
    baseline, out, specimen_dir = map(local_path, [args.baseline_dir, args.output_dir, args.specimen_dir])
    if not specimen_dir.is_relative_to(ROOT / "data/processed"):
        parser.error("Specimen-level records must remain under data/processed.")
    if any(path.exists() for path in [out, specimen_dir]):
        parser.error("Output destinations already exist; choose new output and specimen directories.")
    started = datetime.now(timezone.utc).isoformat()
    for item in records():
        verify(local_path(item["file"]), item)
    baseline_manifest_path = baseline / "run_manifest.json"
    baseline_manifest = json.loads(baseline_manifest_path.read_text(encoding="utf-8"))
    if baseline_manifest["input_manifest_sha256"] != digest(ROOT / "data/manifest.json"):
        raise ValueError("Baseline run used a different public-source manifest.")
    baseline_artifacts = {item["file"]: item for item in baseline_manifest["artifacts"]}

    def verified_baseline(name: str) -> Path:
        relative = (baseline / name).relative_to(ROOT).as_posix()
        if relative not in baseline_artifacts:
            raise ValueError(f"Baseline manifest does not record {relative}.")
        path = local_path(relative)
        verify(path, baseline_artifacts[relative])
        return path

    raw = ROOT / "data/raw/rejection_public"
    _, meta = read_geo_matrix(raw / "GSE212160_series_matrix.txt.gz")
    counts, batches = read_rcc_archive(raw / "GSE212160_RAW.tar", specimen_ids=meta.index)
    normalized = normalize_counts(counts)
    split_path = verified_baseline("biopsy_split.csv")
    frozen_path = verified_baseline("any_rejection_frozen.json")
    importance_path = verified_baseline("any_rejection_gene_importance.csv")
    split = pd.read_csv(split_path, index_col="sample")
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    selected = frozen["selected_model"]
    prediction_path = verified_baseline(f"any_rejection_{selected}_test_predictions.csv")
    predictions = pd.read_csv(prediction_path, index_col="sample").rename(columns={"probability": "rejection_score"})
    if (not np.isfinite(predictions.rejection_score.to_numpy(dtype=float)).all()
            or not predictions.rejection_score.between(0, 1).all()
            or predictions.predicted.dtype != bool
            or not np.isfinite(frozen["threshold"]) or not 0 <= frozen["threshold"] <= 1):
        raise ValueError("Saved scores and threshold must be finite in [0, 1], with boolean flags.")
    if meta.index.has_duplicates or set(meta.index) != set(split.index):
        raise ValueError("Metadata and fixed split must contain the same unique specimens.")
    diagnosis = meta["histology diganosis of rejection"]
    if not diagnosis.isin(DIAGNOSES).all() or not meta.cohort.isin(COHORTS).all():
        raise ValueError("Unexpected diagnosis or cohort.")
    if not split.loc[meta.index, "histology"].equals(diagnosis.rename("histology")):
        raise ValueError("Fixed split diagnoses differ from source metadata.")
    validation_ids = meta.index[meta.cohort.eq("Validation cohort sample")]
    if predictions.index.has_duplicates or set(predictions.index) != set(validation_ids):
        raise ValueError("Predictions must cover exactly the author validation specimens.")
    predictions = predictions.loc[validation_ids]
    if not np.array_equal(predictions.y, diagnosis.loc[validation_ids].ne("No Rejection").astype(int)):
        raise ValueError("Prediction labels do not agree with source metadata.")
    if not np.array_equal(predictions.predicted, predictions.rejection_score.ge(frozen["threshold"])):
        raise ValueError("Saved flags do not agree with the frozen threshold.")
    predictions["error_group"] = np.select(
        [predictions.y.eq(1) & predictions.predicted,
         predictions.y.eq(1) & ~predictions.predicted,
         predictions.y.eq(0) & predictions.predicted],
        ["Correct rejection flag", "Missed rejection", "False rejection flag"],
        default="Correct no-rejection result")
    frame = normalized[TARGETS].copy()
    for target in TARGETS:
        frame[f"{target} raw count"] = counts[target]
    frame["cohort"] = meta.cohort.map(COHORTS)
    frame["diagnosis"] = diagnosis
    frame["split"] = split.loc[frame.index, "split"]
    frame = frame.join(predictions[["rejection_score", "predicted", "error_group"]]).join(batches)
    # A descriptive, post-evaluation cutoff, not an assay positivity criterion.
    frame["both_BK_signals_above_zero"] = frame[TARGETS].gt(0).all(axis=1)
    cohorts = summaries(frame, ["cohort", "diagnosis"])
    errors = summaries(frame.loc[validation_ids], ["error_group"])
    high = frame.groupby(["cohort", "diagnosis"], observed=True).both_BK_signals_above_zero.agg(n="size", both_above_zero="sum").reset_index()
    high["fraction"] = high.both_above_zero / high.n
    high_errors = frame.loc[validation_ids].groupby("error_group").both_BK_signals_above_zero.agg(n="size", both_above_zero="sum").reset_index()
    batch_rows = []
    for column in ["Date", "CartridgeID", "ScannerID"]:
        discovery_values = set(batches.loc[meta.cohort.eq("Discovery cohort sample"), column])
        validation_values = set(batches.loc[validation_ids, column])
        batch_rows.append({"field": column, "discovery_distinct": len(discovery_values),
                           "validation_distinct": len(validation_values), "shared_distinct": len(discovery_values & validation_values)})
    batch_overlap = pd.DataFrame(batch_rows)
    source_fields = [name for name in meta.columns if name != "histology_diagnosis"]
    metadata_inventory = [{"field": name, "origin": "GEO sample metadata", "n_present": int(meta[name].notna().sum()),
                           "n_distinct": int(meta[name].nunique()), "values_if_at_most_10": sorted(map(str, meta[name].dropna().unique())) if meta[name].nunique() <= 10 else []}
                          for name in source_fields]
    metadata_inventory += [{"field": name, "origin": "RCC header", "n_present": int(batches[name].notna().sum()),
                            "n_distinct": int(batches[name].nunique()), "values_if_at_most_10": sorted(map(str, batches[name].dropna().unique())) if batches[name].nunique() <= 10 else []}
                           for name in batches.columns]
    importance = pd.read_csv(importance_path)
    importance["rank"] = np.arange(1, len(importance) + 1)
    viral_importance = importance.loc[importance.gene.isin(TARGETS)]
    out.mkdir(parents=True, exist_ok=True)
    specimen_dir.mkdir(parents=True, exist_ok=True)
    write_csv(cohorts, out / "signals_by_cohort_diagnosis.csv")
    write_csv(errors, out / "signals_by_validation_error.csv")
    write_csv(high, out / "higher_signal_counts.csv")
    write_csv(high_errors, out / "higher_signal_error_counts.csv")
    write_csv(batch_overlap, out / "batch_cohort_overlap.csv")
    write_csv(viral_importance, out / "viral_feature_importance.csv")
    write_csv(frame.rename_axis("specimen_id").reset_index(), specimen_dir / "viral_specimen_review.csv")
    (out / "metadata_inventory.json").write_text(json.dumps(metadata_inventory, indent=2), encoding="utf-8")
    (out / "sources.json").write_text(json.dumps(SOURCES, indent=2), encoding="utf-8")
    rows = []
    for cohort in COHORTS.values():
        for histology in DIAGNOSES:
            values = cohorts.loc[cohorts.cohort.eq(cohort) & cohorts.diagnosis.eq(histology)].set_index("target")
            tail = high.loc[high.cohort.eq(cohort) & high.diagnosis.eq(histology)].iloc[0]
            cells = [f"{values.loc[target, 'median']:.2f} ({values.loc[target, 'p25']:.2f} to {values.loc[target, 'p75']:.2f})" for target in TARGETS]
            rows.append([cohort, histology, str(int(tail.n)), *cells, str(int(tail.both_above_zero))])
    error_rows = []
    for error_group, values in errors.groupby("error_group"):
        values = values.set_index("target")
        error_rows.append([error_group, str(int(values.iloc[0].n)), *[f"{values.loc[target, 'median']:.2f}" for target in TARGETS]])
    no_rejection_high = high.loc[high.diagnosis.eq("No Rejection")].set_index("cohort")
    discovery_high = int(no_rejection_high.loc["Discovery", "both_above_zero"])
    validation_high = int(no_rejection_high.loc["Author technical validation", "both_above_zero"])
    nonrejection_discovery = int(high.loc[high.cohort.eq("Discovery") & high.diagnosis.eq("No Rejection"), "n"].iloc[0])
    nonrejection_validation = int(high.loc[high.cohort.eq("Author technical validation") & high.diagnosis.eq("No Rejection"), "n"].iloc[0])
    rejection_high = int(high.loc[high.diagnosis.ne("No Rejection"), "both_above_zero"].sum())
    tail = higher_signal_outcomes(frame.loc[validation_ids])
    importance_description = "; ".join(
        f"{row.gene}: rank {int(row.rank)}, importance {row.importance:.2f}"
        for row in viral_importance.itertuples(index=False))
    report = f"""# BK targets and study composition

This descriptive follow-up reviews the frozen `{selected}` model from `{args.baseline_dir}`. It does not fit a model, change its features, choose a new operating threshold, or diagnose infection. Re-run with `uv run python scripts/review_viral_targets.py --output-dir results/analysis/NEW_viral --specimen-dir data/processed/analysis/NEW_viral`.

## Main finding

The saved importance table ranks the two BK targets as follows: {importance_description}. The B-HOT panel includes viral targets; these measurements are not human genes. [Banff B-HOT consensus, Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC7496585/).

Among specimens labeled no rejection, {discovery_high}/{nonrejection_discovery} discovery specimens and {validation_high}/{nonrejection_validation} author-validation specimens have both normalized BK signals above zero. Across both cohorts, {rejection_high} specimens labeled rejection also meet that reference. Of the {tail['n']} validation specimens above the reference, {tail['negative_results']} received a no-rejection result; there were {tail['false_flags']} false flags and {tail['missed_rejection']} missed rejection cases. These counts describe the relationship between BK signals, recorded diagnosis, and the model's results. Importance alone does not establish the direction, the reason for the association, or an individual feature's causal contribution.

Zero is a descriptive reference for the normalized scale: `count + 1` exceeds the geometric mean of the 12 `housekeeping count + 1` values. It is not an infection cutoff or a detection limit. The reference was used after reviewing results, for description only. Full quantiles and raw-count ranges are in `signals_by_cohort_diagnosis.csv`.

## Cohort and diagnosis

Values are median normalized signal (25th to 75th percentile), using the shared specimen-level normalization. The last column counts specimens where both BK signals exceed zero.

{markdown_table(["Cohort", "Recorded diagnosis", "n", "BK large T Ag", "BK VP1", "Both > 0"], rows)}

The broad no-rejection label may combine different non-rejection conditions. The study's Supplementary Table S3 explicitly compares its T-cell-mediated histologic class with allograft polyomavirus nephropathy samples within its NVH histologic class. The public sample metadata available here does not identify which individual specimens have that diagnosis. [Zhang et al., Supplementary Table S3](https://ars.els-cdn.com/content/image/1-s2.0-S0023683723002477-mmc5.docx).

## Selected-model errors in author validation

The table shows median normalized signals; full ranges and quantiles are in `signals_by_validation_error.csv`.

{markdown_table(["Result", "n", "BK large T Ag", "BK VP1"], error_rows)}

There are {tail['missed_rejection']} missed rejection cases and {tail['false_flags']} false flags with both BK signals above zero. These aggregate comparisons describe associations and cannot assign a reason to an individual mistake. A feature-removal experiment would be separate follow-up modeling, and was not done here.

## Available metadata and limits

The GEO metadata contains title, source tissue, histology, tissue, and author cohort. It supplies no confirmed infection indicator, viral load, patient identifier, transplant-center identifier, or detailed no-rejection subtype. The parser preserves the source's `histology diganosis of rejection` spelling and also exposes a corrected internal alias. `metadata_inventory.json` lists fields and completeness. [GSE212160 deposit](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212160).

The RCC headers expose assay metadata. Discovery uses 37 assay dates and 96 cartridges; validation uses 7 dates and 31 cartridges, with no shared dates or cartridges. All specimens use one scanner. Thus author cohort and those batches are linked; this comparison cannot separately estimate their effects. The training/screening split within discovery is a specimen split, not a held-out batch, patient, or center split. Do not infer independent patients or centers from distinct sample or cartridge identifiers.

The authors discuss extraction-protocol and sample-age comparisons in their Supplementary Methods, but those per-specimen variables are not supplied in the GEO characteristics used here. No claim about their effects is derived from these aggregate summaries. [Zhang et al., Supplementary Methods](https://ars.els-cdn.com/content/image/1-s2.0-S0023683723002477-mmc6.docx).

## Reproduction and records

Public inputs are checked against `data/manifest.json`, and used baseline artifacts are checked against the completed baseline run manifest before reading. `manifest.json` records inputs and their hashes, the shared source-code hashes, the frozen threshold, and outputs. The only specimen-level export is `{args.specimen_dir}/viral_specimen_review.csv`, under ignored local data. This review uses the project's own raw RCC measurements and saved predictions; it does not use the deposited batch-corrected expression matrix as predictors. The cited supplements supply background context; local copies are optional for reproducing the numeric results, and their availability is recorded.
"""
    (out / "REPORT.md").write_text(report, encoding="utf-8")
    input_paths = [ROOT / "data/manifest.json", raw / "GSE212160_series_matrix.txt.gz", raw / "GSE212160_RAW.tar", split_path, prediction_path,
                   frozen_path, importance_path, baseline_manifest_path]
    source_paths = [Path(__file__), ROOT / "src/kidney_biopsy/preprocessing.py", ROOT / "src/kidney_biopsy/source.py"]
    record = lambda path: {"file": path.relative_to(ROOT).as_posix(), "sha256": digest(path), "bytes": path.stat().st_size}
    reference_paths = [ROOT / "data/reference/study/rejection_source_manifest.json", ROOT / "data/reference/study/rejection_supplement_5.txt",
                       ROOT / "data/reference/study/rejection_supplement_6.txt"]
    optional_references = [{"file": path.relative_to(ROOT).as_posix(), "available": path.is_file(), **(record(path) if path.is_file() else {})}
                           for path in reference_paths]
    manifest = {"started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(), "analysis": "descriptive follow-up; no fitting or threshold change",
                "selected_model": selected, "frozen_threshold": frozen["threshold"], "n_specimens": len(frame), "n_validation": len(validation_ids),
                "higher_signal_reference": "both normalized BK signals > 0; descriptive, not infection criterion", "inputs": [record(path) for path in input_paths],
                "optional_local_references": optional_references, "python": platform.python_version(), "dependencies": {name: version(name) for name in ["numpy", "pandas"]},
                "environment_lock": record(ROOT / "uv.lock"), "source_code": [record(path) for path in source_paths],
                "outputs": [record(path) for directory in [out, specimen_dir] for path in sorted(directory.iterdir()) if path.is_file()]}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Reviewed {len(frame)} specimens, including {len(validation_ids)} author-validation predictions. Report: {out.relative_to(ROOT).as_posix()}/REPORT.md")


if __name__ == "__main__":
    main()
