"""Verify a fresh, physically copied project and its installed prediction app.

The copy receives source, the public input files, and this project's selected
model artifacts. It creates its own virtual environment and package cache. It
does not retrain models. All paths supplied by the caller are project-relative;
completed check directories and evidence are preserved.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from verify_local_data import ROOT, local_path, records, sha256, verify

COPY_DIRS = ("src/kidney_biopsy", "scripts", "tests", "experiments", "docs", ".github", "data/demo")
COPY_FILES = (
    "README.md",
    "AGENTS.md",
    "pyproject.toml",
    "uv.lock",
    ".python-version",
    ".gitignore",
    "data/manifest.json",
)


def source_files() -> list[Path]:
    selected = [local_path(name) for name in COPY_FILES]
    for name in COPY_DIRS:
        directory = local_path(name)
        if directory.exists():
            selected.extend(
                path
                for path in directory.rglob("*")
                if path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix not in {".pyc", ".pyo"}
            )
    return sorted(set(selected))


def runtime_files(run_name: str) -> list[Path]:
    run = local_path(run_name)
    manifest_path = run / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frozen_path = run / "any_rejection_frozen.json"
    model_path = local_path(manifest["model_dir"]) / "any_rejection_selected_model.joblib"
    artifacts = {item["file"]: item for item in manifest["artifacts"]}
    if len(artifacts) != len(manifest["artifacts"]):
        raise ValueError("Selected run contains duplicate artifact paths.")
    selected = [manifest_path]
    for path in (frozen_path, model_path):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in artifacts:
            raise ValueError("Selected model and metadata must be in the run manifest.")
        verify(local_path(relative), artifacts[relative])
        selected.append(path)
    # The model information route may display small aggregate evaluation files.
    # Preserve their original hashes; specimen tables and training snapshots are
    # unnecessary to exercise the installed application.
    for item in manifest["artifacts"]:
        path = local_path(item["file"])
        if (
            path.parent == run
            and path.suffix in {".json", ".csv"}
            and not any(
                word in path.name
                for word in (
                    "_test_predictions",
                    "_screen_predictions",
                    "biopsy_split",
                    "raw_batch",
                )
            )
        ):
            verify(path, item)
            selected.append(path)
    for item in records():
        path = local_path(item["file"])
        verify(path, item)
        selected.append(path)
    return sorted(set(selected))


def copy_inputs(destination: Path, files: list[Path]) -> list[dict]:
    copied = []
    for source in sorted(set(files)):
        relative = source.relative_to(ROOT).as_posix()
        source = local_path(relative)  # Reject linked files and parent directories.
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open("rb") as read_stream, target.open("xb") as write_stream:
            shutil.copyfileobj(read_stream, write_stream)
        source_hash = sha256(source)
        if sha256(target) != source_hash:
            raise ValueError(f"Physical copy differs from its source: {relative}")
        copied.append({"file": relative, "bytes": target.stat().st_size, "sha256": source_hash})
    return copied


def clean_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "VIRTUAL_ENV",
        "UV_PROJECT_ENVIRONMENT",
        "UV_PYTHON",
        "UV_CACHE_DIR",
        "MPLCONFIGDIR",
        "KIDNEY_BIOPSY_PROJECT_ROOT",
        "KIDNEY_BIOPSY_RESULTS_DIR",
        "KIDNEY_BIOPSY_DEMO_DIR",
    ):
        environment.pop(name, None)
    return environment


def run_step(command: list[str], root: Path, environment: dict, *, timeout: int = 600) -> dict:
    started = time.perf_counter()
    print(f"Running in fresh project: {' '.join(command)}", flush=True)
    completed = subprocess.run(
        command, cwd=root, env=environment, capture_output=True, text=True, timeout=timeout
    )
    step = {
        "command": command,
        "returncode": completed.returncode,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    if completed.returncode:
        # Only command diagnostics are printed; no submitted assay CSV is logged.
        print(completed.stdout[-4000:], end="", file=sys.stderr)
        print(completed.stderr[-4000:], end="", file=sys.stderr)
    return step


def check_copy(run_name: str, output_name: str) -> None:
    """Run only inside the newly installed copy, using its model and raw data."""
    import importlib.resources

    import numpy as np
    import pandas as pd
    from fastapi.testclient import TestClient

    import kidney_biopsy
    from kidney_biopsy.api import create_app
    from kidney_biopsy.prediction import load_predictor
    from kidney_biopsy.source import read_rcc_archive

    prefix = Path(sys.prefix).resolve()
    package_path = Path(kidney_biopsy.__file__).resolve()
    if prefix != (ROOT / ".venv").resolve() or not package_path.is_relative_to(prefix):
        raise ValueError("Fresh check must use the copy's own environment and installed package.")
    output = local_path(output_name)
    if output.exists():
        raise ValueError("Application check output already exists.")
    predictor = load_predictor(ROOT, run_name)
    counts, _ = read_rcc_archive(ROOT / "data/raw/rejection_public/GSE212160_RAW.tar")
    sample = counts.iloc[:2]
    sample_name = "data/processed/setup_application/counts.csv"
    csv_output_name = "data/processed/setup_application/cli_predictions.csv"
    sample_path = local_path(sample_name)
    sample_path.parent.mkdir(parents=True, exist_ok=False)
    sample.to_csv(sample_path, index_label="specimen")
    cli = subprocess.run(
        [
            sys.executable,
            "-m",
            "kidney_biopsy",
            "--counts-csv",
            sample_name,
            "--results-dir",
            run_name,
            "--output",
            csv_output_name,
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if cli.returncode:
        raise ValueError("Fresh application's CLI prediction failed.")
    expected = pd.read_csv(local_path(csv_output_name), dtype={"specimen": str})
    pages = {}
    with TestClient(create_app(project_root=ROOT, run_dir=run_name)) as client:
        for route in ("/", "/assets/style.css", "/assets/app.js", "/health", "/model"):
            response = client.get(route)
            if response.status_code != 200 or not response.content:
                raise ValueError(f"Fresh application failed to serve {route}.")
            pages[route] = response.status_code
        info = client.get("/model").json()
        if (
            info["model_version"] != predictor.model_version
            or info["threshold"] != predictor.threshold
        ):
            raise ValueError("API model metadata differs from the selected model.")
        if (
            info["required_targets"] != list(predictor.schema.required_targets)
            or not info["evaluation"]
        ):
            raise ValueError("API is missing its assay contract or verified evaluation summary.")
        response = client.post(
            "/predict", content=sample_path.read_bytes(), headers={"Content-Type": "text/csv"}
        )
        if response.status_code != 200:
            raise ValueError("API rejected the valid source specimens.")
        actual = pd.DataFrame(response.json()["predictions"])
        if actual.specimen.tolist() != expected.specimen.tolist():
            raise ValueError("CLI/API specimen order differs.")
        np.testing.assert_allclose(
            actual.rejection_score, expected.rejection_score, rtol=0, atol=1e-12
        )
        np.testing.assert_allclose(actual.threshold, expected.threshold, rtol=0, atol=1e-12)
        for field in ("rejection_flag", "model_version", "schema_version", "input_check"):
            if actual[field].tolist() != expected[field].tolist():
                raise ValueError(f"CLI/API output differs: {field}")
        invalid = sample.drop(columns=predictor.schema.features[0]).to_csv(index_label="specimen")
        invalid_response = client.post(
            "/predict", content=invalid, headers={"Content-Type": "text/csv"}
        )
        invalid_body = invalid_response.json()
        if not (
            400 <= invalid_response.status_code < 500
            and "error" in invalid_body
            and "predictions" not in invalid_body
        ):
            raise ValueError("Invalid batch did not produce a structured whole-batch rejection.")
    assets = importlib.resources.files("kidney_biopsy").joinpath("static")
    summary = {
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "successful": True,
        "run_dir": run_name,
        "model_version": predictor.model_version,
        "environment": prefix.relative_to(ROOT).as_posix(),
        "package": package_path.relative_to(ROOT).as_posix(),
        "installed_static_assets": [
            name
            for name in ("index.html", "style.css", "app.js")
            if assets.joinpath(name).is_file()
        ],
        "routes": pages,
        "specimens": len(expected),
        "numeric_tolerance": 1e-12,
        "evaluation_source": info["evaluation"]["source"],
        "max_absolute_score_difference": float(
            np.max(np.abs(actual.rejection_score - expected.rejection_score))
        ),
        "invalid_batch_status": invalid_response.status_code,
        "invalid_batch_error_code": invalid_body["error"]["code"],
        "raw_counts_logged": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2)
        stream.write("\n")
    print(
        f"PASS: fresh installed application scored {len(expected)} specimens and rejected invalid input."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default="results/reproduction/20260915_shared")
    parser.add_argument(
        "--check-dir", default=None, help="New folder under data/processed/setup_checks/."
    )
    parser.add_argument("--output", default=None, help="New aggregate verification JSON path.")
    parser.add_argument("--check-copy", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.check_copy:
        check_copy(args.run_dir, args.output or "results/checks/fresh/application.json")
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    workspace = local_path(args.check_dir or f"data/processed/setup_checks/{stamp}")
    allowed = local_path("data/processed/setup_checks")
    if workspace == allowed or not workspace.is_relative_to(allowed):
        raise ValueError("Fresh check must have its own folder below data/processed/setup_checks/.")
    if workspace.exists():
        raise ValueError("Fresh check directory exists; choose a new --check-dir.")
    output = local_path(args.output or f"results/checks/{stamp}/fresh_setup.json")
    if output.exists():
        raise ValueError("Verification record exists; choose a new --output path.")
    files = source_files() + runtime_files(args.run_dir)
    uv = shutil.which("uv")
    if not uv:
        raise ValueError("uv must be installed and available on PATH.")
    started = time.perf_counter()
    fresh_root = workspace / "project"
    fresh_root.mkdir(parents=True)
    record = {
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "successful": False,
        "copied_project": fresh_root.relative_to(ROOT).as_posix(),
        "run_dir": args.run_dir,
        "steps": [],
        "errors": [],
        "scope": "Fresh dependency installation, physical local inputs, software tests, and installed CLI/API. No model retraining or container run.",
    }
    try:
        record["copied_files"] = copy_inputs(fresh_root, files)
        environment = clean_environment()
        environment["UV_CACHE_DIR"] = str(fresh_root / ".uv-cache")
        environment["UV_PROJECT_ENVIRONMENT"] = str(fresh_root / ".venv")
        commands = [
            ["uv", "sync", "--frozen", "--no-editable", "--python", "3.12"],
            ["uv", "run", "--no-sync", "python", "experiments/rejection_public/download.py"],
            ["uv", "run", "--no-sync", "python", "scripts/verify_local_data.py"],
            [
                "uv",
                "run",
                "--no-sync",
                "python",
                "scripts/check_project.py",
                "--require-installed",
                "--output",
                "results/checks/fresh/checks.json",
            ],
            [
                "uv",
                "run",
                "--no-sync",
                "python",
                "scripts/verify_fresh_setup.py",
                "--check-copy",
                "--run-dir",
                args.run_dir,
                "--output",
                "results/checks/fresh/application.json",
            ],
        ]
        for command in commands:
            step = run_step([uv, *command[1:]], fresh_root, environment)
            step["command"] = command
            record["steps"].append(step)
            if step["returncode"]:
                raise ValueError(f"Fresh setup step failed: {' '.join(command)}")
        for key, name in (("software_checks", "checks.json"), ("application", "application.json")):
            record[key] = json.loads(
                (fresh_root / "results/checks/fresh" / name).read_text(encoding="utf-8")
            )
        record["successful"] = True
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        record["errors"].append(f"{type(error).__name__}: {error}")
    record["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
    print(f"{'PASS' if record['successful'] else 'FAIL'}: {output.relative_to(ROOT).as_posix()}")
    if not record["successful"]:
        for error in record["errors"]:
            print(error, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
