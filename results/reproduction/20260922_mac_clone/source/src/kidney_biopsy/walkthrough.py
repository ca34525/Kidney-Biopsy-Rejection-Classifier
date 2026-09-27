"""Explain one prepared public specimen using the service's actual preprocessing."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .prediction import Predictor
from .preprocessing import DIAGNOSES, normalize_counts


def describe_specimen(counts: pd.DataFrame, item: dict, predictor: Predictor) -> dict:
    """Keep public labels separate from the measurements passed to the model."""
    if len(counts) != 1 or counts.index[0] != item.get("specimen"):
        raise ValueError("Walkthrough specimen differs from the prepared example.")
    diagnosis = item.get("recorded_diagnosis")
    if diagnosis not in DIAGNOSES:
        raise ValueError("Walkthrough needs a known recorded diagnosis.")
    if item.get("model_version") != predictor.model_version:
        raise ValueError("Prepared example model differs from the configured model.")
    if "IFNG" not in predictor.schema.features:
        raise ValueError("Walkthrough needs the IFNG assay target.")

    # Use the same transformation as prediction; the displayed arithmetic only
    # explains one target. The entire ordered panel is passed to the fitted model.
    normalized = normalize_counts(counts, predictor.schema)
    log_counts = np.log2(counts.astype(float) + 1).iloc[0]
    housekeeping = [
        {
            "target": target,
            "raw_count": float(counts.iloc[0][target]),
            "log2_count_plus_one": float(log_counts[target]),
        }
        for target in predictor.schema.housekeeping_targets
    ]
    prediction = predictor.predict_normalized(normalized).to_dict(orient="records")[0]
    return {
        "example_id": item["id"],
        "specimen": item["specimen"],
        "recorded_diagnosis": diagnosis,
        "recorded_rejection": bool(DIAGNOSES[diagnosis]),
        "model_version": predictor.model_version,
        "schema_version": predictor.schema.schema_version,
        "preprocessing_version": predictor.schema.preprocessing_version,
        "threshold": predictor.threshold,
        "required_targets": len(predictor.schema.required_targets),
        "predictor_targets": len(predictor.schema.features),
        "normalization": {
            "illustrated_target": "IFNG",
            "raw_count": float(counts.iloc[0]["IFNG"]),
            "log2_count_plus_one": float(log_counts["IFNG"]),
            "housekeeping_mean": float(
                log_counts[list(predictor.schema.housekeeping_targets)].mean()
            ),
            "normalized_value": float(normalized.iloc[0]["IFNG"]),
            "housekeeping": housekeeping,
        },
        "prediction": prediction,
    }
