"""Check local training artifacts and independent inference against this run's evaluation."""

import argparse
import csv
import json
import math
from datetime import datetime, timezone

from verify_local_data import local_path, sha256


def read_rows(path, key):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    mapping = {row[key]: row for row in rows}
    if not rows or len(mapping) != len(rows):
        raise ValueError(f"Empty output or duplicate specimen IDs: {path.name}")
    return mapping


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default="results/reproduction/baseline")
    parser.add_argument("--inference-csv", default="results/reproduction/baseline/inference.csv")
    parser.add_argument(
        "--output",
        default=None,
        help="New verification JSON path; defaults to a timestamped results/verification directory.",
    )
    args = parser.parse_args()
    run_dir = local_path(args.run_dir)
    manifest = json.loads((run_dir / "run_manifest.json").read_text())
    for item in manifest["artifacts"]:
        path = local_path(item["file"])
        if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise ValueError(f"Run artifact does not match its training manifest: {item['file']}")
    source_status = []
    source_items = manifest.get("sources", [manifest["source"], manifest["environment_lock"]])
    for item in source_items:
        path = local_path(item["file"])
        current_hash = sha256(path) if path.is_file() else None
        snapshot = item.get("snapshot")
        if snapshot and sha256(local_path(snapshot)) != item["sha256"]:
            raise ValueError(f"Preserved run source snapshot changed: {snapshot}")
        source_status.append(
            {
                "file": item["file"],
                "recorded_sha256": item["sha256"],
                "current_sha256": current_hash,
                "current_matches_run": current_hash == item["sha256"],
                "snapshot": snapshot,
            }
        )
    frozen = json.loads((run_dir / "any_rejection_frozen.json").read_text())
    expected = read_rows(
        run_dir / f"any_rejection_{frozen['selected_model']}_test_predictions.csv", "sample"
    )
    actual = read_rows(local_path(args.inference_csv), "specimen")
    if expected.keys() != actual.keys() or len(actual) != frozen["test_n"]:
        raise ValueError("Inference and evaluation specimen IDs differ.")
    differences = []
    predicted_positive = 0
    for specimen, row in actual.items():
        score = float(row["rejection_score"])
        difference = abs(score - float(expected[specimen]["probability"]))
        if not math.isfinite(score) or difference > 1e-12:
            raise ValueError(f"Inference probability mismatch: {specimen}")
        flag = row["rejection_flag"] == "True"
        if flag != (expected[specimen]["predicted"] == "True") or flag != (
            score >= frozen["threshold"]
        ):
            raise ValueError(f"Inference class mismatch: {specimen}")
        differences.append(difference)
        predicted_positive += flag
    summary = {
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "run_dir": args.run_dir,
        "inference_csv": args.inference_csv,
        "inference_sha256": sha256(local_path(args.inference_csv)),
        "run_manifest_sha256": sha256(run_dir / "run_manifest.json"),
        "verified_artifacts": len(manifest["artifacts"]),
        "specimens": len(actual),
        "max_absolute_probability_difference": max(differences),
        "predicted_positive": predicted_positive,
        "predicted_negative": len(actual) - predicted_positive,
        "threshold": frozen["threshold"],
        "numeric_tolerance": 1e-12,
        "source_status": source_status,
        "source_note": "Changed current source or lockfiles are recorded as development since the run; immutable artifacts and available source snapshots must still match their hashes.",
        "comparison": "Shared inference versus evaluation produced by this local training run.",
    }
    output_name = (
        args.output
        or f"results/verification/{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}/inference_verification.json"
    )
    output = local_path(output_name)
    if output.is_relative_to(run_dir):
        raise ValueError("Write verification outside the completed run directory.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
