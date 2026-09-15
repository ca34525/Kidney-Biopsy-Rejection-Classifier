"""Run fast software checks without public data or fitted research artifacts.

Run from the project root after uv sync --frozen. JSON evidence is written to a
new path even when a check fails. CI installs a wheel with --no-editable and also
requires package imports and static assets to come from that environment.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.metadata
import importlib.resources
import json
from pathlib import Path
import platform
import sys
import time
import tomllib
import unittest

from verify_local_data import ROOT, local_path, sha256

SOURCE_DIRS = ("src/kidney_biopsy", "scripts", "tests", "experiments")
STATIC_ASSETS = ("index.html", "style.css", "app.js")


def python_sources() -> list[Path]:
    return sorted(path for folder in SOURCE_DIRS for path in (ROOT / folder).rglob("*.py")
                  if "__pycache__" not in path.parts)


def check_environment(require_installed: bool) -> dict:
    import kidney_biopsy

    if sys.version_info[:2] != (3, 12):
        raise ValueError("Checks require Python 3.12.")
    package_path = Path(kidney_biopsy.__file__).resolve()
    environment = Path(sys.prefix).resolve()
    if not environment.is_relative_to(ROOT):
        raise ValueError("Use this project's own virtual environment.")
    if not package_path.is_relative_to(ROOT):
        raise ValueError("Package import came from outside this project.")
    if require_installed and not package_path.is_relative_to(environment):
        raise ValueError("Expected an installed package; run uv sync --frozen --no-editable.")
    assets = importlib.resources.files("kidney_biopsy").joinpath("static")
    for name in STATIC_ASSETS:
        if not assets.joinpath(name).is_file() or not assets.joinpath(name).read_bytes():
            raise ValueError(f"Missing or empty packaged application asset: {name}")
        if assets.joinpath(name).read_bytes() != (ROOT / "src/kidney_biopsy/static" / name).read_bytes():
            raise ValueError(f"Installed application asset differs from this source: {name}")
    return {
        "python": platform.python_version(),
        "environment": environment.relative_to(ROOT).as_posix(),
        "package": package_path.relative_to(ROOT).as_posix(),
        "installed_package_required": require_installed,
        "static_assets": list(STATIC_ASSETS),
        "package_versions": {name: importlib.metadata.version(name) for name in (
            "kidney-biopsy-rejection-classifier", "numpy", "pandas", "scikit-learn",
            "catboost", "fastapi", "uvicorn", "httpx")},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-installed", action="store_true")
    parser.add_argument("--output", default=None, help="New project-relative JSON evidence path.")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = local_path(args.output or f"results/checks/{stamp}/checks.json")
    if output.exists():
        raise ValueError("Check record already exists; choose a new --output path.")
    started = time.perf_counter()
    record = {"verified_utc": datetime.now(timezone.utc).isoformat(),
              "successful": False, "errors": [], "checks": {}}
    try:
        files = python_sources()
        evidence_files = [*files, ROOT / "pyproject.toml", ROOT / "uv.lock",
                          ROOT / ".github/workflows/checks.yml",
                          *(ROOT / "src/kidney_biopsy/static" / name for name in STATIC_ASSETS)]
        record["sources"] = [{"file": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)}
                             for path in evidence_files if path.is_file()]
        for path in files:
            compile(path.read_bytes(), path.relative_to(ROOT).as_posix(), "exec")
        for name in ("pyproject.toml", "uv.lock"):
            tomllib.loads((ROOT / name).read_text(encoding="utf-8"))
        record["checks"]["syntax"] = {"python_files": len(files), "toml_files": 2}
        record["checks"]["environment"] = check_environment(args.require_installed)
        (ROOT / ".uv-cache").mkdir(exist_ok=True)
        # Tests import research scripts, while kidney_biopsy stays an installed
        # package: the project root contains no top-level kidney_biopsy module.
        sys.path.insert(0, str(ROOT))
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        record["checks"]["tests"] = {
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "successful": result.wasSuccessful(),
            "failed_tests": [test.id() for test, _ in result.failures + result.errors],
        }
        record["successful"] = result.wasSuccessful() and result.testsRun > 0
    except Exception as error:
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
