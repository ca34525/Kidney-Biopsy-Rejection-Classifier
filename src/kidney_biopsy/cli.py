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
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--counts-csv")
    source.add_argument("--geo-validation", action="store_true")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--results-dir", default="results/reproduction/baseline")
    parser.add_argument("--model-dir", default=None)
    parser.add_argument("--output", default="data/processed/predictions/inference.csv")
    args = parser.parse_args(argv)
    try:
        root = Path(args.project_root).resolve()
        predictor = load_predictor(root, args.results_dir, args.model_dir)
        output = project_path(root, args.output)
        if output.exists():
            raise ValueError("Output already exists; choose a new --output path to preserve prior results.")
        if args.geo_validation:
            manifest = json.loads((root / "data/manifest.json").read_text(encoding="utf-8-sig"))
            for item in manifest:
                verify_artifact(root, item)
            raw_dir = root / "data/raw/rejection_public"
            _, meta = read_geo_matrix(raw_dir / "GSE212160_series_matrix.txt.gz")
            counts, _ = read_rcc_archive(raw_dir / "GSE212160_RAW.tar", specimen_ids=meta.index)
            counts = counts.loc[meta["cohort"].eq("Validation cohort sample")]
        else:
            path = project_path(root, args.counts_csv)
            if path.stat().st_size > MAX_UPLOAD_BYTES:
                raise ValueError("CSV exceeds the 20 MiB upload limit.")
            counts = read_counts_csv(path, predictor.schema)
        predictions = predictor.predict(counts)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", newline="", encoding="utf-8") as stream:
            predictions.to_csv(stream, index=False)
        print(f"Wrote {len(predictions)} research predictions to {args.output}")
    except (ValueError, OSError, KeyError) as error:
        print(f"Prediction failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
