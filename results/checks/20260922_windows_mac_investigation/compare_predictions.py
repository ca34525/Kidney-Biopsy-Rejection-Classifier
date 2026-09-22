"""Compare saved specimen-level outputs without changing either original run."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def compare(old, new, keys, numeric):
    a = pd.read_csv(old, float_precision="round_trip").set_index(keys)
    b = pd.read_csv(new, float_precision="round_trip").set_index(keys)
    assert a.index.is_unique and b.index.is_unique and set(a.index) == set(b.index)
    b = b.loc[a.index]
    assert list(a.columns) == list(b.columns)
    assert a.notna().all().all() and b.notna().all().all()
    return {
        "rows": len(a),
        "changed_labels_or_flags": {c: int((a[c] != b[c]).sum()) for c in a
                                    if c not in numeric and (a[c] != b[c]).any()},
        "max_numeric_differences": {c: float(np.max(np.abs(a[c] - b[c]))) for c in a
                                    if c in numeric},
    }


def main():
    windows = Path("../Windows Original")
    result = {"primary": {}, "stability": {}, "subtypes": {}, "inputs": {}, "source": {}}
    for path in sorted((windows / "results/reproduction/20260915_shared").glob("*_predictions.csv")):
        result["primary"][path.name] = compare(
            path, Path("results/reproduction/20260922_mac_clone") / path.name,
            ["sample"], ["probability", "rejection_score"],
        )
    for i in range(1, 21):
        old = windows / f"data/processed/stability/20260917_stability/repeat_{i:02d}"
        new = Path(f"data/processed/stability/20260922_mac_clone/repeat_{i:02d}")
        for name in ["screen_predictions.csv", "assessment_predictions.csv"]:
            result["stability"][f"{i:02d}/{name}"] = compare(
                old / name, new / name, ["sample", "model"], ["score", "threshold"]
            )
    for name in ["author_validation_scores.csv", "discovery_screen_scores.csv"]:
        old = windows / "data/processed/analysis/20260915_subtypes" / name
        new = Path("data/processed/analysis/20260922_mac_clone_subtypes") / name
        columns = pd.read_csv(old, nrows=0).columns
        result["subtypes"][name] = compare(old, new, ["sample"],
                                            [c for c in columns if c.endswith("_score")])
    for path in Path("data/raw/rejection_public").iterdir():
        result["inputs"][path.name] = {
            "mac_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "windows_sha256": hashlib.sha256((windows / path).read_bytes()).hexdigest(),
        }
    for name in ["experiments/rejection_public/run.py", "experiments/rejection_stability/run.py",
                 "experiments/rejection_subtypes/run.py", "src/kidney_biopsy/preprocessing.py",
                 "src/kidney_biopsy/source.py", "uv.lock", "pyproject.toml"]:
        result["source"][name] = {
            "same_text_ignoring_line_endings": Path(name).read_text() == (windows / name).read_text()
        }
    out = Path("results/checks/20260922_windows_mac_investigation/prediction_comparison.json")
    out.write_text(json.dumps(result, indent=2) + "\n")
    for group in ["primary", "stability", "subtypes"]:
        rows = result[group]
        print(group, "tables:", len(rows), "rows:", sum(r["rows"] for r in rows.values()),
              "changed flags/labels:", {k: r["changed_labels_or_flags"] for k, r in rows.items()
                                        if r["changed_labels_or_flags"]})


if __name__ == "__main__":
    main()
