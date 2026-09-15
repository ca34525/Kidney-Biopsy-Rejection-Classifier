"""Batch raw B-HOT CSV prediction with the configured local research model.

Run from the project root. CSV input has one specimen per row, specimen ID first,
then all frozen assay targets and 12 housekeeping targets. Extra columns are
rejected. The caller must supply compatible assay measurements. CSV batches are
limited to 1,000 specimens and 20 MiB; invalid batches return no predictions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .preprocessing import read_counts_csv
from .prediction import load_predictor, project_path, verify_artifact
from .source import read_geo_matrix, read_rcc_archive

MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    input_options = parser.add_mutually_exclusive_group(required=True)
    input_options.add_argument("--counts-csv")
    input_options.add_argument("--geo-validation", action="store_true")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--results-dir", default="results/reproduction/baseline")
    parser.add_argument("--model-dir", default=None)
    parser.add_argument("--output", default="data/processed/predictions/inference.csv")
    args = parser.parse_args(argv)

    try:
        root = Path(args.project_root).resolve()
        predictor = load_predictor(root, args.results_dir, args.model_dir)
        output_path = project_path(root, args.output)
        if output_path.exists():
            raise ValueError(
                "Output already exists; choose a new --output path to preserve prior results."
            )

        if args.geo_validation:
            manifest_path = root / "data/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            for item in manifest:
                verify_artifact(root, item)
            raw_dir = root / "data/raw/rejection_public"
            _, metadata = read_geo_matrix(raw_dir / "GSE212160_series_matrix.txt.gz")
            counts, _ = read_rcc_archive(
                raw_dir / "GSE212160_RAW.tar", specimen_ids=metadata.index
            )
            counts = counts.loc[metadata["cohort"].eq("Validation cohort sample")]
        else:
            counts_path = project_path(root, args.counts_csv)
            if counts_path.stat().st_size > MAX_UPLOAD_BYTES:
                raise ValueError("CSV exceeds the 20 MiB upload limit.")
            counts = read_counts_csv(counts_path, predictor.schema)

        predictions = predictor.predict(counts)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("x", newline="", encoding="utf-8") as stream:
            predictions.to_csv(stream, index=False)
        print(f"Wrote {len(predictions)} research predictions to {args.output}")
    except (ValueError, OSError, KeyError) as error:
        print(f"Prediction failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
