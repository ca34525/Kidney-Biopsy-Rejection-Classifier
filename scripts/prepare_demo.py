"""Prepare small public CSV examples from this project's verified raw inputs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from kidney_biopsy.prediction import load_predictor, project_path, sha256, verify_artifact
from kidney_biopsy.source import read_geo_matrix, read_rcc_archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--results-dir", default="results/reproduction/20260915_shared")
    parser.add_argument("--output-dir", default="data/demo")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    output = project_path(root, args.output_dir)
    if output.exists():
        raise SystemExit(
            "Demo output already exists; use a new --output-dir to preserve prepared files."
        )
    source_manifest = json.loads((root / "data/manifest.json").read_text(encoding="utf-8-sig"))
    for item in source_manifest:
        verify_artifact(root, item)
    predictor = load_predictor(root, args.results_dir)
    run = project_path(root, args.results_dir)
    run_manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
    split_path = run / "biopsy_split.csv"
    split_record = next(
        item
        for item in run_manifest["artifacts"]
        if item["file"] == split_path.relative_to(root).as_posix()
    )
    verify_artifact(root, split_record)
    split = pd.read_csv(split_path, index_col=0)
    raw = root / "data/raw/rejection_public"
    _, metadata = read_geo_matrix(raw / "GSE212160_series_matrix.txt.gz")
    counts, _ = read_rcc_archive(raw / "GSE212160_RAW.tar", specimen_ids=metadata.index)
    examples = []
    diagnoses = [
        ("no-rejection", "No Rejection"),
        ("antibody-mediated", "Antibody-mediated Rejection"),
        ("t-cell-mediated", "T cell-mediated Rejection"),
        ("mixed", "Mixed Rejection"),
    ]
    selected = []
    for ident, diagnosis in diagnoses:
        eligible = split.index[
            split["split"].eq("discovery_screen")
            & metadata.loc[split.index, "histology_diagnosis"].eq(diagnosis)
        ]
        if len(eligible) == 0:
            raise ValueError(f"No screening example for {diagnosis}.")
        specimen = sorted(eligible)[0]
        selected.append(
            (
                ident,
                diagnosis,
                specimen,
                counts.loc[[specimen], list(predictor.schema.required_targets)],
            )
        )
    output.mkdir(parents=True)
    for ident, diagnosis, specimen, frame in selected:
        path = output / f"{ident}.csv"
        frame.to_csv(path, index_label="specimen")
        examples.append(
            {
                "id": ident,
                "label": diagnosis,
                "description": f"Public discovery-screen specimen; recorded diagnosis: {diagnosis}.",
                "valid": True,
                "specimen": specimen,
                "recorded_diagnosis": diagnosis,
                "file": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    invalid = selected[0][3].drop(columns="IFNG")
    path = output / "missing-target.csv"
    invalid.to_csv(path, index_label="specimen")
    examples.append(
        {
            "id": "missing-target",
            "label": "Invalid: missing IFNG",
            "description": "The public no-rejection example with one required target removed.",
            "valid": False,
            "file": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    )
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_manifest": "data/manifest.json",
        "source_manifest_sha256": sha256(root / "data/manifest.json"),
        "source_files": source_manifest,
        "run_dir": args.results_dir,
        "model_version": predictor.model_version,
        "split_artifact": split_record,
        "selection": "First accession in lexical order within each recorded diagnosis in the saved discovery-screen split. Scores did not guide selection.",
        "examples": examples,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(examples)} public examples in {args.output_dir}")


if __name__ == "__main__":
    main()
