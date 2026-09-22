"""One controlled refit of the differing candidate; no saved run is changed."""

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from experiments.rejection_stability.run import (
    SEEDS,
    configuration,
    discovery_data,
    make_candidates,
    read_geo_matrix,
    read_rcc_archive,
    split_discovery,
)


def main():
    root = Path.cwd()
    raw = root / "data/raw/rejection_public"
    _, metadata = read_geo_matrix(raw / "GSE212160_series_matrix.txt.gz")
    counts, _ = read_rcc_archive(raw / "GSE212160_RAW.tar", specimen_ids=metadata.index)
    metadata, features, labels = discovery_data(metadata, counts)
    parts = split_discovery(metadata, SEEDS[5])
    x = features.loc[parts["screen"]]
    model = make_candidates(configuration())["catboost_depth6"]
    model.fit(features.loc[parts["fit"]], labels.loc[parts["fit"]])
    scores = model.predict_proba(x)[:, 1]
    result = {
        "procedure": "One unchanged depth-6 refit of stability repetition 6 on Mac.",
        "seed": SEEDS[5],
        "candidate_parameters": model.get_params(),
        "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in raw.iterdir()},
        "comparisons": {},
    }
    for name, directory in [
        ("windows", root.parent / "Windows Original/data/processed/stability/20260917_stability/repeat_06"),
        ("mac", root / "data/processed/stability/20260922_mac_clone/repeat_06"),
    ]:
        old = joblib.load(directory / "catboost_depth6.joblib")
        old_scores = old.predict_proba(x)[:, 1]
        saved = pd.read_csv(directory / "screen_predictions.csv", float_precision="round_trip")
        saved = saved.loc[saved.model.eq("catboost_depth6")].set_index("sample").loc[x.index]
        assignments = pd.read_csv(directory / "assignments.csv")
        result["comparisons"][name] = {
            "saved_model_on_mac_vs_saved_scores": float(np.max(np.abs(old_scores - saved.score))),
            "refit_vs_saved_model_on_same_inputs": float(np.max(np.abs(scores - old_scores))),
            "assignment_rows": len(assignments),
        }
    result["mac_and_windows_assignments_equal"] = pd.read_csv(
        root.parent / "Windows Original/data/processed/stability/20260917_stability/repeat_06/assignments.csv"
    ).equals(pd.read_csv(root / "data/processed/stability/20260922_mac_clone/repeat_06/assignments.csv"))
    out = root / "results/checks/20260922_windows_mac_investigation/repeat_six.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
