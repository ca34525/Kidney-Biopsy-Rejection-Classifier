"""Load a configured project model and apply the same scoring path as training.

joblib artifacts are trusted project files, never caller uploads. Manifest hashes
detect changed files; they are not authentication for an untrusted manifest.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import joblib
import numpy as np
import pandas as pd

from .preprocessing import AssaySchema, _validate_identifiers, normalize_counts

DEFAULT_RUN = "results/reproduction/20260915_shared"


def project_path(project_root: str | Path, relative: str) -> Path:
    root = Path(project_root).resolve()
    relative_path = PurePosixPath(relative)
    if (
        not relative
        or "\\" in relative
        or ":" in relative
        or relative_path.is_absolute()
        or ".." in relative_path.parts
    ):
        raise ValueError(f"Expected a project-relative path: {relative!r}")
    path = root.joinpath(*relative_path.parts)
    for component in [path, *path.parents]:
        if component == root:
            break
        if component.is_symlink() or component.is_junction():
            raise ValueError(f"Linked paths are not allowed: {relative}")
    if not path.resolve().is_relative_to(root):
        raise ValueError("Path escapes the project folder.")
    return path


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_artifact(project_root: str | Path, item: dict) -> Path:
    path = project_path(project_root, item["file"])
    if not path.is_file() or path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
        raise ValueError(f"Artifact differs from its recorded manifest: {item['file']}")
    return path


def _check_model_features(model: Any, features) -> None:
    expected_features = list(features)
    model_features = getattr(model, "feature_names_in_", None)
    if model_features is None:
        model_features = getattr(model, "feature_names_", None)
    if model_features is None or list(model_features) != expected_features:
        raise ValueError("Model feature names or order do not match the frozen assay schema.")

    feature_count = getattr(model, "n_features_in_", len(expected_features))
    # CatBoost's joblib reload can report n_features_in_=0 while retaining all
    # feature_names_. The exact ordered names above remain the contract check.
    if feature_count not in (0, len(expected_features)):
        raise ValueError("Model feature count does not match the frozen assay schema.")

    classes = np.asarray(getattr(model, "classes_", []))
    if classes.shape != (2,) or not np.array_equal(classes, [0, 1]):
        raise ValueError("Model must expose binary classes in order [0, 1].")


def predict_scores(model: Any, normalized_features: pd.DataFrame) -> np.ndarray:
    """Score named, normalized features; shared by training evaluation and inference."""
    _validate_identifiers(normalized_features)
    _check_model_features(model, normalized_features.columns)
    try:
        feature_values = normalized_features.to_numpy(dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError("Normalized assay values must be numeric.") from error
    if not np.isfinite(feature_values).all():
        raise ValueError("Normalized assay values must be finite.")

    class_scores = np.asarray(model.predict_proba(normalized_features), dtype=float)
    if (
        class_scores.shape != (len(normalized_features), 2)
        or not np.isfinite(class_scores).all()
        or (class_scores < 0).any()
        or (class_scores > 1).any()
        or not np.allclose(class_scores.sum(axis=1), 1, rtol=0, atol=1e-7)
    ):
        raise ValueError("Model returned invalid binary scores.")
    return class_scores[:, 1]


@dataclass(frozen=True)
class Predictor:
    model: Any
    schema: AssaySchema
    threshold: float
    model_version: str
    target: str = "any_rejection"

    def __post_init__(self):
        if not np.isfinite(self.threshold) or not 0 <= self.threshold <= 1:
            raise ValueError("Frozen threshold must be finite and between zero and one.")
        if (
            self.target != "any_rejection"
            or not isinstance(self.model_version, str)
            or not self.model_version.strip()
        ):
            raise ValueError("Prediction needs the any-rejection target and a model version.")
        _check_model_features(self.model, self.schema.features)

    def predict(self, counts: pd.DataFrame) -> pd.DataFrame:
        """Validate an entire raw batch before returning any specimen results."""
        normalized = normalize_counts(counts, self.schema)
        return self.predict_normalized(normalized)

    def predict_normalized(self, features: pd.DataFrame) -> pd.DataFrame:
        """Internal/research entry point; applications should call predict(raw_counts)."""
        if list(features.columns) != list(self.schema.features):
            raise ValueError("Normalized feature order differs from the frozen schema.")
        scores = predict_scores(self.model, features)
        return pd.DataFrame(
            {
                "specimen": features.index,
                "rejection_score": scores,
                "rejection_flag": scores >= self.threshold,
                "threshold": self.threshold,
                "model_version": self.model_version,
                "schema_version": self.schema.schema_version,
                "input_check": "passed",
            }
        )


def load_predictor(
    project_root: str | Path, run_dir: str, model_dir: str | None = None
) -> Predictor:
    """Load a trusted, project-controlled completed run; verify before deserialization.

    The legacy baseline has no explicit schema version. Its feature list is treated
    as the original v1 contract, and its content hash supplies a stable model version.
    Later changes to research source files do not invalidate immutable run artifacts.
    """
    root = Path(project_root).resolve()
    results_dir = project_path(root, run_dir)
    manifest_path = results_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    configured_model_dir = manifest["model_dir"]
    if model_dir is not None:
        requested_directory = project_path(root, model_dir)
        recorded_directory = project_path(root, configured_model_dir)
        if requested_directory != recorded_directory:
            raise ValueError("Model directory does not match the selected training run.")

    model_path = project_path(root, configured_model_dir) / "any_rejection_selected_model.joblib"
    frozen_path = results_dir / "any_rejection_frozen.json"
    artifacts_by_path = {item["file"]: item for item in manifest["artifacts"]}
    if len(artifacts_by_path) != len(manifest["artifacts"]):
        raise ValueError("Training manifest contains duplicate artifact paths.")
    for path in (frozen_path, model_path):
        relative_path = path.relative_to(root).as_posix()
        if relative_path not in artifacts_by_path:
            raise ValueError("Model and frozen metadata must be recorded in the training manifest.")
        verify_artifact(root, artifacts_by_path[relative_path])

    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    if "schema" in frozen:
        schema = AssaySchema.from_dict(frozen["schema"])
        if list(schema.features) != frozen["features"]:
            raise ValueError("Frozen features disagree with the assay schema.")
    else:
        schema = AssaySchema(features=tuple(frozen["features"]))
    for field in ("schema_version", "preprocessing_version"):
        if field in frozen and frozen[field] != getattr(schema, field):
            raise ValueError(f"Frozen {field} is incompatible with the assay schema.")
    if "required_targets" in frozen and frozen["required_targets"] != list(schema.required_targets):
        raise ValueError("Frozen required targets disagree with the assay schema.")

    model = joblib.load(model_path)
    model_version = frozen.get("model_version")
    if not model_version:
        model_version = f"{frozen['selected_model']}-{sha256(model_path)[:12]}"
    return Predictor(
        model=model,
        schema=schema,
        threshold=float(frozen["threshold"]),
        model_version=model_version,
        target=frozen["target"],
    )
