"""Reproduce the fixed biopsy experiment with discovery-only model selection.

Run: uv run python experiments/rejection_public/run.py

Read the workflow in run_experiment(): prepare the data, fit candidates on the
training split, then freeze and evaluate each target. Raw counts are normalized
within each specimen. Metadata and identifiers never enter the predictors.

This repeats the fixed baseline recipe; its evaluation results have already
been seen. Completed runs retain their own source, settings, and artifacts.
"""
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import platform
import shutil
import sys
import time

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.feature_selection import SelectKBest, f_classif
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

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/rejection_public"


def choose_threshold(labels, model_scores, sensitivity=0.90):
    """Keep the highest cutoff that retains the required screening positives."""
    positive_scores = model_scores[labels == 1]
    candidates = np.unique(model_scores)
    return float(max(
        cutoff for cutoff in candidates
        if (positive_scores >= cutoff).mean() >= sensitivity
    ))


def summarize_scores(labels, model_scores, cutoff):
    true_negative, false_positive, false_negative, true_positive = confusion_matrix(
        labels, model_scores >= cutoff, labels=[0, 1]
    ).ravel()
    return {
        "n": int(len(labels)),
        "positives": int(sum(labels)),
        "roc_auc": float(roc_auc_score(labels, model_scores)),
        "average_precision": float(average_precision_score(labels, model_scores)),
        "threshold": float(cutoff),
        "sensitivity": float(true_positive / (true_positive + false_negative)),
        "specificity": float(true_negative / (true_negative + false_positive)),
        "ppv": (
            float(true_positive / (true_positive + false_positive))
            if true_positive + false_positive else None
        ),
        "npv": (
            float(true_negative / (true_negative + false_negative))
            if true_negative + false_negative else None
        ),
        "tp": int(true_positive),
        "fp": int(false_positive),
        "tn": int(true_negative),
        "fn": int(false_negative),
        "accuracy": float((true_positive + true_negative) / len(labels)),
        "brier": float(np.mean((labels - model_scores) ** 2)),
    }


def make_candidates(feature_count):
    """Create fresh models for one target, in the fixed screening order."""
    def catboost(depth):
        return CatBoostClassifier(
            iterations=300,
            depth=depth,
            learning_rate=0.04,
            loss_function="Logloss",
            verbose=False,
            thread_count=3,
            random_seed=2026,
            allow_writing_files=False,
        )

    return {
        "catboost_all_depth4": catboost(4),
        "catboost_all_depth6": catboost(6),
        "catboost_top50": make_pipeline(
            SelectKBest(f_classif, k=min(50, feature_count)),
            catboost(4),
        ),
        "catboost_top200": make_pipeline(
            SelectKBest(f_classif, k=min(200, feature_count)),
            catboost(4),
        ),
        "logistic_all": make_pipeline(
            StandardScaler(),
            LogisticRegression(C=0.1, max_iter=2000),
        ),
        "logistic_top50": make_pipeline(
            SelectKBest(f_classif, k=min(50, feature_count)),
            StandardScaler(),
            LogisticRegression(C=0.1, max_iter=2000),
        ),
        "extra_trees": ExtraTreesClassifier(
            n_estimators=400,
            min_samples_leaf=3,
            max_features=0.3,
            n_jobs=3,
            random_state=2026,
        ),
        "hist_boosting": HistGradientBoostingClassifier(
            max_iter=150,
            max_leaf_nodes=7,
            l2_regularization=5,
            random_state=2026,
        ),
        "single_gene_IFNG": make_pipeline(
            StandardScaler(),
            LogisticRegression(C=1, max_iter=1000),
        ),
    }


def prepare_data(output_dir):
    """Read the raw assay, save the fixed split, and check specimen overlap."""
    _, metadata = read_geo_matrix(RAW / "GSE212160_series_matrix.txt.gz")
    raw_counts, batches = read_rcc_archive(
        RAW / "GSE212160_RAW.tar", specimen_ids=metadata.index
    )
    features = normalize_counts(raw_counts)
    batches.to_csv(output_dir / "raw_batch_identifiers.csv")

    if features.shape != (1395, 758):
        raise ValueError(
            f"Expected 1,395 specimens and 758 assay predictors, received {features.shape}."
        )
    expected_cohorts = {
        "Discovery cohort sample": 1050,
        "Validation cohort sample": 345,
    }
    if metadata["cohort"].value_counts(dropna=False).to_dict() != expected_cohorts:
        raise ValueError("Unexpected or missing source cohort membership.")

    diagnoses = metadata["histology diganosis of rejection"].rename("histology_diagnosis")
    binary_labels = map_diagnoses(diagnoses)
    discovery_ids = metadata.index[metadata["cohort"].eq("Discovery cohort sample")]
    evaluation_ids = metadata.index[metadata["cohort"].eq("Validation cohort sample")]
    training_ids, screening_ids = train_test_split(
        discovery_ids.to_numpy(),
        test_size=0.25,
        stratify=diagnoses.loc[discovery_ids].to_numpy(),
        random_state=20260915,
    )
    # Preserve train_test_split's row order as well as each specimen's assignment.
    split_ids = {
        "train": training_ids,
        "discovery_screen": screening_ids,
        "author_validation": evaluation_ids,
    }
    assignments = pd.Series("author_validation", index=metadata.index)
    assignments.loc[training_ids] = "train"
    assignments.loc[screening_ids] = "discovery_screen"
    pd.DataFrame({
        "sample": metadata.index,
        "split": assignments,
        "histology": diagnoses,
        "title": metadata.title,
    }).to_csv(output_dir / "biopsy_split.csv", index=False)

    duplicate_profiles = features.duplicated(keep=False)
    if duplicate_profiles.any():
        profile_hashes = pd.util.hash_pandas_object(features, index=False)
        profile_splits = pd.DataFrame({
            "profile": profile_hashes, "split": assignments,
        }).groupby("profile")["split"].nunique()
        if profile_splits.gt(1).any():
            raise ValueError(
                "Identical molecular profiles cross training/screening/evaluation splits."
            )
    audit = {
        "included_specimens": len(metadata),
        "excluded_specimens": 0,
        "predictor_count": len(features.columns),
        "cohorts": expected_cohorts,
        "duplicate_normalized_profiles": int(duplicate_profiles.sum()),
        "cross_split_duplicate_profiles": 0,
        "class_counts": pd.crosstab(assignments, diagnoses).to_dict(orient="index"),
        "sample_join": "GEO and raw RCC specimen sets match exactly; each appears once.",
        "predictors": (
            "Assay targets only; housekeeping targets, diagnosis, cohort, IDs, and batch excluded."
        ),
    }
    (output_dir / "data_audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )
    print(
        "COUNTS", len(training_ids), len(screening_ids), len(evaluation_ids),
        len(features.columns), "duplicate_normalized_profiles",
        duplicate_profiles.sum(), flush=True,
    )
    targets = {
        "any_rejection": binary_labels,
        "antibody_mediated_component": diagnoses.isin([
            "Antibody-mediated Rejection", "Mixed Rejection",
        ]).astype(int),
        "t_cell_mediated_component": diagnoses.isin([
            "T cell-mediated Rejection", "Mixed Rejection",
        ]).astype(int),
    }
    return features, targets, split_ids


def fit_candidates(target, labels, features, split_ids):
    """Fit on training rows; choose each candidate's cutoff on screening rows."""
    training_ids = split_ids["train"]
    screening_ids = split_ids["discovery_screen"]
    screening_labels = labels.loc[screening_ids].to_numpy()
    fitted_models = make_candidates(features.shape[1])
    screening_results = []

    for name, model in fitted_models.items():
        candidate_features = features[["IFNG"]] if name == "single_gene_IFNG" else features
        started = time.time()
        model.fit(candidate_features.loc[training_ids], labels.loc[training_ids])
        model_scores = predict_scores(model, candidate_features.loc[screening_ids])
        cutoff = choose_threshold(screening_labels, model_scores)

        feature_count = candidate_features.shape[1]
        if hasattr(model, "named_steps") and "selectkbest" in model.named_steps:
            feature_count = int(model.named_steps["selectkbest"].get_support().sum())
        result = {
            "target": target,
            "model": name,
            "features": feature_count,
            **summarize_scores(screening_labels, model_scores, cutoff),
            "seconds": time.time() - started,
        }
        screening_results.append(result)
        print("SCREEN", json.dumps(result), flush=True)

    return fitted_models, screening_results


def freeze_and_evaluate(
    target, labels, features, split_ids, fitted_models, screening_results,
    output_dir, model_dir,
):
    """Save the discovery choice before evaluating the selected model and baselines."""
    training_ids = split_ids["train"]
    screening_ids = split_ids["discovery_screen"]
    evaluation_ids = split_ids["author_validation"]

    # IFNG is a separate simple benchmark. AUC breaks specificity ties among
    # multivariable candidates; the fitted model is retained without refitting.
    eligible = [row for row in screening_results if row["model"] != "single_gene_IFNG"]
    selected = max(eligible, key=lambda row: (row["specificity"], row["roc_auc"]))
    selected_name = selected["model"]
    selected_model = fitted_models[selected_name]
    frozen = {
        "target": target,
        "selected_model": selected_name,
        "threshold": selected["threshold"],
        "selection": "Max discovery-screen specificity at >=90% sensitivity, then AUC; no refit.",
        "train_n": len(training_ids),
        "screen_n": len(screening_ids),
        "test_n": len(evaluation_ids),
        "features": list(features.columns),
        "schema": AssaySchema(features=tuple(features.columns)).to_dict(),
        "model_version": f"{output_dir.name}:{target}:{selected_name}",
    }
    (output_dir / f"{target}_frozen.json").write_text(
        json.dumps(frozen, indent=2), encoding="utf-8"
    )

    # Author-validation scoring starts only after the choice and threshold are saved.
    evaluation_results = {}
    evaluation_labels = labels.loc[evaluation_ids].to_numpy()
    comparison_names = dict.fromkeys([selected_name, "single_gene_IFNG", "logistic_all"])
    for name in comparison_names:
        screening_result = next(row for row in screening_results if row["model"] == name)
        cutoff = screening_result["threshold"]
        model = fitted_models[name]
        candidate_features = features[["IFNG"]] if name == "single_gene_IFNG" else features

        screening_scores = predict_scores(model, candidate_features.loc[screening_ids])
        pd.DataFrame({
            "sample": screening_ids,
            "y": labels.loc[screening_ids],
            "rejection_score": screening_scores,
            "predicted": screening_scores >= cutoff,
        }).to_csv(output_dir / f"{target}_{name}_screen_predictions.csv", index=False)
        joblib.dump(model, model_dir / f"{target}_{name}.joblib")

        evaluation_scores = predict_scores(model, candidate_features.loc[evaluation_ids])
        evaluation_results[name] = summarize_scores(
            evaluation_labels, evaluation_scores, cutoff
        )
        # Keep the historical CSV column name for compatibility with saved runs.
        pd.DataFrame({
            "sample": evaluation_ids,
            "y": labels.loc[evaluation_ids],
            "probability": evaluation_scores,
            "predicted": evaluation_scores >= cutoff,
        }).to_csv(output_dir / f"{target}_{name}_test_predictions.csv", index=False)

    constant_scores = np.full(len(evaluation_ids), float(labels.loc[training_ids].mean()))
    evaluation_results["training_prevalence"] = summarize_scores(
        evaluation_labels, constant_scores, 0.5
    )
    evaluation_results["prevalence_all_positive"] = summarize_scores(
        evaluation_labels, constant_scores, 0
    )
    print("FINAL", target, json.dumps(evaluation_results), flush=True)

    joblib.dump(selected_model, model_dir / f"{target}_selected_model.joblib")
    if hasattr(selected_model, "save_model"):
        selected_model.save_model(str(model_dir / f"{target}_selected_model.cbm"))
    if target == "any_rejection" and hasattr(selected_model, "feature_importances_"):
        pd.DataFrame({
            "gene": features.columns,
            "importance": selected_model.feature_importances_,
        }).sort_values("importance", ascending=False).to_csv(
            output_dir / "any_rejection_gene_importance.csv", index=False
        )

    return {
        "selected_model": selected_name,
        "screen": selected,
        "author_validation": evaluation_results,
    }


def run_experiment(output_dir, model_dir):
    """Use the same prepared data and split for all three recorded targets."""
    features, targets, split_ids = prepare_data(output_dir)
    results_by_target = {}
    all_screening_results = []
    for target, labels in targets.items():
        fitted_models, screening_results = fit_candidates(
            target, labels, features, split_ids
        )
        all_screening_results.extend(screening_results)
        pd.DataFrame(all_screening_results).to_csv(
            output_dir / "biopsy_screen.csv", index=False
        )
        results_by_target[target] = freeze_and_evaluate(
            target, labels, features, split_ids, fitted_models, screening_results,
            output_dir, model_dir,
        )
        (output_dir / "biopsy_results.json").write_text(
            json.dumps(results_by_target, indent=2), encoding="utf-8"
        )
    print("FINISHED", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="results/reproduction/baseline")
    parser.add_argument("--model-dir", default="data/processed/models/baseline")
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_local_data import local_path, records, sha256, verify

    output_dir = local_path(args.output_dir)
    model_dir = local_path(args.model_dir)
    if (output_dir / "run_manifest.json").exists() or (output_dir / "biopsy_results.json").exists():
        parser.error(
            "This output directory already contains a run; choose a new --output-dir and --model-dir."
        )
    if model_dir.exists() and any(model_dir.iterdir()):
        parser.error("The model directory must be empty; choose a new --model-dir.")
    for item in records():
        verify(local_path(item["file"]), item)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    start_time = time.perf_counter()

    configuration = {
        "procedure": (
            "Reproduction of baseline models, discovery split, selection, and thresholds; "
            "shared preprocessing/prediction extraction."
        ),
        "target": "Any recorded rejection, plus two secondary component targets.",
        "normalization": (
            "log2(raw count + 1) minus within-specimen mean of 12 log2(housekeeping count + 1) values."
        ),
        "discovery_split": {
            "test_size": 0.25, "stratify": "four original diagnoses", "random_state": 20260915,
        },
        "threshold_rule": "Highest screening score threshold retaining at least 90% of rejection cases.",
        "selection_rule": "Maximum screening specificity, then ROC-AUC; fitted model retained without refitting.",
        "models": {
            "catboost_all_depth4": {
                "iterations": 300, "depth": 4, "learning_rate": 0.04, "random_seed": 2026,
            },
            "catboost_all_depth6": {
                "iterations": 300, "depth": 6, "learning_rate": 0.04, "random_seed": 2026,
            },
            "catboost_top50": {
                "selection": "f_classif on training only", "k": 50,
                "catboost": "catboost_all_depth4",
            },
            "catboost_top200": {
                "selection": "f_classif on training only", "k": 200,
                "catboost": "catboost_all_depth4",
            },
            "logistic_all": {
                "scaler": "StandardScaler fitted on training only", "C": 0.1, "max_iter": 2000,
            },
            "logistic_top50": {
                "selection": "f_classif on training only", "k": 50, "logistic": "logistic_all",
            },
            "extra_trees": {
                "n_estimators": 400, "min_samples_leaf": 3,
                "max_features": 0.3, "random_state": 2026,
            },
            "hist_boosting": {
                "max_iter": 150, "max_leaf_nodes": 7,
                "l2_regularization": 5, "random_state": 2026,
            },
            "single_gene_IFNG": {
                "scaler": "StandardScaler fitted on training only", "C": 1, "max_iter": 1000,
            },
        },
        "constant_baseline": "Training-label prevalence as score; threshold 0.5 (majority prediction).",
    }
    (output_dir / "configuration.json").write_text(
        json.dumps(configuration, indent=2), encoding="utf-8"
    )

    # Preserve the executable source and lockfile before fitting.
    sources = [
        Path(__file__),
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
        ROOT / "scripts/verify_local_data.py",
        *sorted((ROOT / "src/kidney_biopsy").glob("*.py")),
    ]
    snapshots = []
    for source in sources:
        relative = source.relative_to(ROOT)
        snapshot = output_dir / "source" / relative
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, snapshot)
        snapshots.append({
            "file": relative.as_posix(),
            "sha256": sha256(source),
            "snapshot": snapshot.relative_to(ROOT).as_posix(),
        })

    run_experiment(output_dir, model_dir)

    # A manifest marks the completed run and records every saved artifact.
    artifacts = []
    for directory in [output_dir, model_dir]:
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.name not in {"run_manifest.json", "run.log"}:
                artifacts.append({
                    "file": path.relative_to(ROOT).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                })
    manifest = {
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": time.perf_counter() - start_time,
        "python": platform.python_version(),
        "dependencies": {
            name: version(name)
            for name in ["catboost", "joblib", "numpy", "pandas", "scikit-learn", "scipy"]
        },
        "input_manifest": "data/manifest.json",
        "input_manifest_sha256": sha256(ROOT / "data/manifest.json"),
        "source": {
            "file": "experiments/rejection_public/run.py",
            "sha256": sha256(Path(__file__)),
        },
        "sources": snapshots,
        "environment_lock": {"file": "uv.lock", "sha256": sha256(ROOT / "uv.lock")},
        "seeds": {
            "discovery_split": 20260915,
            "catboost": 2026,
            "extra_trees": 2026,
            "hist_boosting": 2026,
        },
        "fit_count": 27,
        "output_dir": args.output_dir,
        "model_dir": args.model_dir,
        "artifacts": artifacts,
        "configuration": "configuration.json",
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
