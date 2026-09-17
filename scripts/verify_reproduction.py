"""Compare a new fixed-procedure training run with preserved baseline predictions."""

import argparse
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from verify_local_data import local_path, sha256


def verify_artifacts(directory):
    manifest = json.loads((directory / "run_manifest.json").read_text())
    for item in manifest["artifacts"]:
        path = local_path(item["file"])
        if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise ValueError(f"Run artifact changed: {item['file']}")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-dir", default="results/reproduction/baseline")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    reference, current, output = map(local_path, (args.reference_dir, args.run_dir, args.output))
    if output.exists():
        parser.error("Verification output exists; choose a new path to preserve the record.")
    manifests = [verify_artifacts(path) for path in (reference, current)]
    summaries = []
    for path in sorted(reference.glob("*_test_predictions.csv")):
        old = pd.read_csv(path).set_index("sample")
        new = pd.read_csv(current / path.name).set_index("sample")
        if not old.index.is_unique or not new.index.is_unique or set(old.index) != set(new.index):
            raise ValueError(f"Prediction specimen IDs differ: {path.name}")
        new = new.loc[old.index]
        if not old[["y", "predicted"]].equals(new[["y", "predicted"]]):
            raise ValueError(f"Prediction labels or flags differ: {path.name}")
        difference = np.abs(old["probability"].to_numpy() - new["probability"].to_numpy())
        if not np.isfinite(difference).all() or np.max(difference) > 1e-12:
            raise ValueError(f"Scores differ beyond 1e-12: {path.name}")
        summaries.append(
            {
                "file": path.name,
                "specimens": len(old),
                "max_absolute_score_difference": float(np.max(difference)),
            }
        )
    if not summaries:
        raise ValueError("No reference predictions found.")
    thresholds = {}
    for path in sorted(reference.glob("*_frozen.json")):
        old, new = [json.loads(p.read_text()) for p in (path, current / path.name)]
        for field in ("selected_model", "threshold", "features", "train_n", "screen_n", "test_n"):
            if old[field] != new[field]:
                raise ValueError(f"Frozen {field} differs: {path.name}")
        thresholds[old["target"]] = old["threshold"]
    old_split = (
        pd.read_csv(reference / "biopsy_split.csv").sort_values("sample").reset_index(drop=True)
    )
    new_split = (
        pd.read_csv(current / "biopsy_split.csv").sort_values("sample").reset_index(drop=True)
    )
    if not old_split.equals(new_split):
        raise ValueError("Actual specimen assignments differ.")
    result = {
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "reference_run": args.reference_dir,
        "reproduced_run": args.run_dir,
        "reference_manifest_sha256": sha256(reference / "run_manifest.json"),
        "reproduced_manifest_sha256": sha256(current / "run_manifest.json"),
        "verified_artifacts": [len(m["artifacts"]) for m in manifests],
        "split_specimens": len(old_split),
        "score_tolerance": 1e-12,
        "selected_thresholds": thresholds,
        "prediction_comparisons": summaries,
        "interpretation": "The shared-code reproduction retained all split assignments, selected models, thresholds, evaluation scores and flags within the stated tolerance.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
