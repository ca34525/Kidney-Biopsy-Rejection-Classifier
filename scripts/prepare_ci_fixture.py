"""Create a tiny synthetic model and demo solely for container checks in CI.

This is not the research model and supplies no evidence about biopsy accuracy.
No public downloads or existing research artifacts are needed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import confusion_matrix

from kidney_biopsy.prediction import project_path, sha256
from kidney_biopsy.preprocessing import HOUSEKEEPING_TARGETS, AssaySchema, normalize_counts


def prepare_fixture(output: Path) -> None:
    if output.exists():
        raise ValueError("CI fixture output already exists; choose a new --output-dir.")
    output.mkdir(parents=True)
    run = output / "results/ci"
    models = output / "data/models"
    demo = output / "data/demo"
    for directory in (run, models, demo):
        directory.mkdir(parents=True)

    def write_json(path: Path, value: dict) -> None:
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def record(path: Path) -> dict:
        return {
            "file": path.relative_to(output).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }

    counts = pd.DataFrame(
        {
            "IFNG": [0.0, 10.0, 50.0, 100.0],
            "CXCL9": [1.0, 8.0, 80.0, 90.0],
            **{target: [1.0, 2.0, 3.0, 4.0] for target in HOUSEKEEPING_TARGETS},
        },
        index=["synthetic-001", "synthetic-002", "synthetic-003", "synthetic-004"],
    )
    schema = AssaySchema(("IFNG", "CXCL9"))
    normalized = normalize_counts(counts, schema)
    labels = [0, 0, 1, 1]
    # Exercise the same native model runtime as the real image, with a tiny fit.
    model = CatBoostClassifier(
        iterations=4,
        depth=2,
        thread_count=1,
        random_seed=20260917,
        allow_writing_files=False,
        verbose=False,
    ).fit(normalized, labels)
    flags = model.predict_proba(normalized)[:, 1] >= 0.5
    tn, fp, fn, tp = (int(value) for value in confusion_matrix(labels, flags).ravel())
    model_path = models / "any_rejection_selected_model.joblib"
    joblib.dump(model, model_path)
    model_version = "synthetic-ci-only"
    frozen_path = run / "any_rejection_frozen.json"
    write_json(
        frozen_path,
        {
            "features": list(schema.features),
            "schema": schema.to_dict(),
            "threshold": 0.5,
            "target": "any_rejection",
            "selected_model": "catboost",
            "model_version": model_version,
        },
    )
    results_path = run / "biopsy_results.json"
    write_json(
        results_path,
        {
            "any_rejection": {
                "selected_model": "catboost",
                "author_validation": {
                    "catboost": {
                        "n": 4,
                        "positives": 2,
                        "fn": fn,
                        "fp": fp,
                        "tp": tp,
                        "tn": tn,
                        "threshold": 0.5,
                        "sensitivity": tp / (tp + fn),
                        "specificity": tn / (tn + fp),
                    }
                },
            }
        },
    )
    write_json(
        run / "run_manifest.json",
        {
            "purpose": "Synthetic fixture for software checks; not research results.",
            "model_dir": "data/models",
            "artifacts": [record(path) for path in (model_path, frozen_path, results_path)],
        },
    )

    examples = []
    for ident, valid, frame in [
        ("valid", True, counts.iloc[[0]]),
        ("missing-target", False, counts.iloc[[0]].drop(columns="IFNG")),
    ]:
        path = demo / f"{ident}.csv"
        frame.to_csv(path, index_label="specimen")
        examples.append(
            {
                "id": ident,
                "label": f"Synthetic CI example: {ident}",
                "description": "Generated software-test data, not a public biopsy specimen.",
                "valid": valid,
                **record(path),
            }
        )
    write_json(
        demo / "manifest.json",
        {
            "run_dir": "results/ci",
            "model_version": model_version,
            "examples": examples,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="build/ci-fixture")
    args = parser.parse_args()
    try:
        prepare_fixture(project_path(Path.cwd(), args.output_dir))
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"Prepared synthetic-ci-only fixture in {args.output_dir}")


if __name__ == "__main__":
    main()
