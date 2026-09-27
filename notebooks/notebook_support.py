"""Small file/provenance helpers; analytical calculations stay in the notebooks."""

from __future__ import annotations

import json
import os
import platform
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import pandas as pd

from kidney_biopsy.prediction import project_path, sha256, verify_artifact
from kidney_biopsy.preprocessing import map_diagnoses
from scripts.verify_local_data import records, verify

ROOT = Path(__file__).resolve().parents[1]
SPLIT_ORDER = ["train", "discovery_screen", "author_validation"]
DIAGNOSIS_ORDER = [
    "No Rejection",
    "Antibody-mediated Rejection",
    "T cell-mediated Rejection",
    "Mixed Rejection",
]
SHORT_DIAGNOSES = ["No rejection", "Antibody-mediated", "T cell-mediated", "Mixed"]
COLORS = ["#176D8A", "#D37B21", "#7B58A3", "#65737E"]
BK_TARGETS = ["BK  large T Ag", "BK  VP1"]


def validate_split(split: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    """Reject wrong joins, diagnoses, or cohort assignments before analysis."""
    if (
        not split.index.is_unique
        or not metadata.index.is_unique
        or split.index.hasnans
        or set(split.index) != set(metadata.index)
    ):
        raise ValueError("Split and metadata must contain exactly the same unique specimens.")
    split = split.loc[metadata.index]
    map_diagnoses(metadata.histology_diagnosis)
    if not split.histology.equals(metadata.histology_diagnosis.rename("histology")):
        raise ValueError("Saved split diagnoses disagree with source metadata.")
    if not split.split.isin(SPLIT_ORDER).all():
        raise ValueError("Unexpected split assignment.")
    expected = metadata.cohort.map(
        {"Discovery cohort sample": False, "Validation cohort sample": True}
    )
    if expected.isna().any() or not split.split.eq("author_validation").equals(expected):
        raise ValueError("Saved split does not preserve the authors' cohorts.")
    return split


class NotebookSession:
    """Verify inputs and record a new descriptive analysis without altering a run."""

    def __init__(self, name: str):
        self.name = name
        self.started = datetime.now(timezone.utc).isoformat()
        self.run_dir = os.environ.get(
            "KIDNEY_BIOPSY_NOTEBOOK_RUN", "results/reproduction/20260915_shared"
        )
        self.run_path = project_path(ROOT, self.run_dir)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        destination = os.environ.get("KIDNEY_BIOPSY_NOTEBOOK_OUTPUT", f"results/notebooks/{stamp}")
        self.output = project_path(ROOT, destination) / name
        if not self.output.is_relative_to(ROOT / "results/notebooks"):
            raise ValueError("Notebook outputs must remain under results/notebooks.")
        self.output.mkdir(parents=True, exist_ok=False)
        self.used = {}

    def remember(self, path: Path) -> Path:
        self.used[path.relative_to(ROOT).as_posix()] = sha256(path)
        return path

    def verify_inputs(self) -> pd.DataFrame:
        entries = records()
        for item in entries:
            path = project_path(ROOT, item["file"])
            verify(path, item)
            self.remember(path)
        self.remember(ROOT / "data/manifest.json")
        return pd.DataFrame(entries)[["file", "bytes", "sha256"]].assign(check="Passed")

    def artifact(self, name: str, *, model: bool = False) -> Path:
        manifest_path = self.remember(self.run_path / "run_manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["input_manifest_sha256"] != sha256(ROOT / "data/manifest.json"):
            raise ValueError("Training run used a different public-source manifest.")
        directory = project_path(ROOT, manifest["model_dir"]) if model else self.run_path
        path = directory / name
        key = path.relative_to(ROOT).as_posix()
        artifacts = {item["file"]: item for item in manifest["artifacts"]}
        if len(artifacts) != len(manifest["artifacts"]) or key not in artifacts:
            raise ValueError(f"Artifact missing or duplicated in run manifest: {key}")
        verify_artifact(ROOT, artifacts[key])
        return self.remember(path)

    def load_split(self, metadata: pd.DataFrame) -> pd.DataFrame:
        split = pd.read_csv(self.artifact("biopsy_split.csv"), index_col="sample")
        return validate_split(split, metadata)

    def table(self, name: str, frame: pd.DataFrame) -> None:
        """Save aggregate tables as JSON (full specimen tables stay out of Git)."""
        self.require_open()
        frame.to_json(self.output / f"{name}.json", orient="table", indent=2)

    def figure(self, name: str, figure) -> None:
        self.require_open()
        figure.savefig(self.output / f"{name}.svg", bbox_inches="tight")
        figure.savefig(self.output / f"{name}.png", dpi=140, bbox_inches="tight")

    def finish(self, findings: dict, configuration: dict | None = None) -> None:
        self.require_open()
        sources = [
            ROOT / "notebooks" / f"{self.name}.ipynb",
            ROOT / "notebooks/notebook_support.py",
            ROOT / "scripts/run_notebooks.py",
            ROOT / "scripts/analyze_results.py",
            ROOT / "experiments/rejection_public/run.py",
            ROOT / "pyproject.toml",
            ROOT / "uv.lock",
            *sorted((ROOT / "src/kidney_biopsy").glob("*.py")),
        ]
        record = {
            "analysis": "Retrospective descriptive notebook addition; no model or threshold changes.",
            "notebook": self.name,
            "run_dir": self.run_dir,
            "started_utc": self.started,
            "finished_utc": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(),
            "packages": {
                name: version(name)
                for name in [
                    "numpy",
                    "pandas",
                    "scikit-learn",
                    "catboost",
                    "matplotlib",
                    "nbclient",
                ]
            },
            "inputs": self.used,
            "sources": {p.relative_to(ROOT).as_posix(): sha256(p) for p in sources},
            "configuration": configuration or {},
            "findings": findings,
            "outputs": {p.name: sha256(p) for p in sorted(self.output.iterdir()) if p.is_file()},
        }
        (self.output / "manifest.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"Evidence saved to {self.output.relative_to(ROOT).as_posix()}")

    def require_open(self) -> None:
        if (self.output / "manifest.json").exists():
            raise FileExistsError(
                "This notebook run is complete; rerun setup for a new output folder."
            )
