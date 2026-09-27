"""Read original Windows models; write only this investigation's local evidence.

Run from the project root with its own environment:
  uv run --frozen python results/checks/20260922_windows_mac_investigation/inspect_models.py

The sibling Windows folder is an explicit audit input, never a service dependency.
No Windows module is imported and no original model is adopted by this project.
"""

import ast
import hashlib
import json
import tempfile
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from kidney_biopsy import normalize_counts, read_geo_matrix, read_rcc_archive

ROOT = Path.cwd()
WINDOWS = ROOT.parent / "Windows Original"
OUT = ROOT / "results/checks/20260922_windows_mac_investigation"
WIN_RUN = "20260915_shared"
MAC_RUN = "20260922_mac_clone"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model_structure(old, new):
    # Temporary JSON exports are deleted; original model files are read only.
    with tempfile.TemporaryDirectory() as temporary:
        paths = [Path(temporary) / f"{i}.json" for i in range(2)]
        for model, path in zip((old, new), paths):
            model.save_model(str(path), format="json")
        a, b = [json.loads(path.read_text()) for path in paths]
    trees_a, trees_b = a["oblivious_trees"], b["oblivious_trees"]
    assert len(trees_a) == len(trees_b)
    # split_index is a reference into each model's complete border collection;
    # compare the actual feature and border, which define the decision.
    def splits(tree):
        return [{k: v for k, v in s.items() if k != "split_index"}
                for s in tree["splits"]]
    changed = [i + 1 for i, (x, y) in enumerate(zip(trees_a, trees_b))
               if splits(x) != splits(y)]
    return {
        "trees": len(trees_a),
        "trees_with_different_decisions": changed,
        "max_leaf_difference": float(np.max(np.abs(
            old.get_leaf_values() - new.get_leaf_values()
        ))),
        "parameters_equal": old.get_all_params() == new.get_all_params(),
        "first_changed_tree": (
            {"number": changed[0], "windows": splits(trees_a[changed[0] - 1]),
             "mac": splits(trees_b[changed[0] - 1])} if changed else None
        ),
    }


def main():
    raw = ROOT / "data/raw/rejection_public"
    _, metadata = read_geo_matrix(raw / "GSE212160_series_matrix.txt.gz")
    counts, _ = read_rcc_archive(raw / "GSE212160_RAW.tar", specimen_ids=metadata.index)
    features = normalize_counts(counts)
    result = {"primary_inference": {}, "structures": {}, "run_source_functions": {}}
    tracked_windows = {}
    for saved in sorted((WINDOWS / f"results/reproduction/{WIN_RUN}").glob("*_test_predictions.csv")):
        name = saved.name.removesuffix("_test_predictions.csv")
        original = WINDOWS / f"data/processed/models/{WIN_RUN}/{name}.joblib"
        tracked_windows[str(original.relative_to(WINDOWS))] = digest(original)
        tracked_windows[str(saved.relative_to(WINDOWS))] = digest(saved)
        old = joblib.load(original)
        new = joblib.load(ROOT / f"data/processed/models/{MAC_RUN}/{name}.joblib")
        reference = pd.read_csv(saved, float_precision="round_trip").set_index("sample")
        x = features.loc[reference.index]
        if name.endswith("single_gene_IFNG"):
            x = x[["IFNG"]]
        old_scores = old.predict_proba(x)[:, 1]
        new_scores = new.predict_proba(x)[:, 1]
        screen = pd.read_csv(WINDOWS / f"results/reproduction/{WIN_RUN}/biopsy_screen.csv",
                             float_precision="round_trip")
        entry = screen.loc[(screen.target + "_" + screen.model).eq(name)].iloc[0]
        result["primary_inference"][name] = {
            "rows": len(reference),
            "original_model_on_mac_vs_original_saved_scores": float(np.max(np.abs(
                old_scores - reference.probability.to_numpy()
            ))),
            "original_model_on_mac_changed_flags": int(np.sum(
                (old_scores >= entry.threshold) != reference.predicted.to_numpy()
            )),
            "windows_vs_mac_models_on_same_mac_inputs": float(np.max(np.abs(
                old_scores - new_scores
            ))),
        }
        if "catboost" in name:
            result["structures"][name] = model_structure(old, new)
    for i in range(1, 21):
        for depth in (4, 6):
            name = f"repeat_{i:02d}/catboost_depth{depth}.joblib"
            original = WINDOWS / f"data/processed/stability/20260917_stability/{name}"
            tracked_windows[str(original.relative_to(WINDOWS))] = digest(original)
            old = joblib.load(original)
            new = joblib.load(ROOT / f"data/processed/stability/{MAC_RUN}/{name}")
            result["structures"][name] = model_structure(old, new)
    for name in ("experiments/rejection_public/run.py", "src/kidney_biopsy/preprocessing.py",
                 "src/kidney_biopsy/source.py"):
        paths = [WINDOWS / "results/reproduction/20260915_readability/source" / name,
                 ROOT / f"results/reproduction/{MAC_RUN}/source" / name]
        # Compare functions/classes separately so import-order formatting is irrelevant.
        definitions = [{node.name: ast.dump(node) for node in ast.parse(p.read_text()).body
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef))} for p in paths]
        result["run_source_functions"][name] = definitions[0] == definitions[1]
    result["windows_file_hashes_unchanged"] = all(
        digest(WINDOWS / path) == before for path, before in tracked_windows.items()
    )
    result["windows_file_hashes"] = tracked_windows
    (OUT / "model_inspection.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Original-model inference:", json.dumps(result["primary_inference"], indent=2))
    print("Different tree decisions:", {
        name: row["trees_with_different_decisions"] for name, row in result["structures"].items()
        if row["trees_with_different_decisions"]
    })
    print("Source function equality:", result["run_source_functions"])
    print("Original files unchanged:", result["windows_file_hashes_unchanged"])


if __name__ == "__main__":
    main()
