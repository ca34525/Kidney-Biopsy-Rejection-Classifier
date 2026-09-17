"""Copy the verified model and public demo files into a new container bundle.

The bundle is a small project root. Original manifests and their relative paths
stay intact; raw training data, other models, and source snapshots are not copied.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path, PurePosixPath

from kidney_biopsy.api import MAX_SPECIMENS, MAX_UPLOAD_BYTES
from kidney_biopsy.prediction import load_predictor, project_path, sha256, verify_artifact
from kidney_biopsy.preprocessing import read_counts_csv


def _path(root: Path, relative: str) -> Path:
    """Require one spelling for each path, including on Windows."""
    path = project_path(root, relative)
    if PurePosixPath(relative).as_posix() != relative:
        raise ValueError(f"Use a normalized project-relative path: {relative!r}")
    return path


def _record(root: Path, path: Path) -> dict:
    return {
        "file": path.relative_to(root).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def prepare_bundle(
    project_root: str | Path = ".",
    run_dir: str = "results/reproduction/20260915_shared",
    demo_dir: str = "data/demo",
    output_dir: str = "build/container",
) -> dict:
    root = Path(project_root).resolve()
    output = _path(root, output_dir)
    if output.exists():
        raise ValueError("Container output already exists; choose a new --output-dir.")
    run = _path(root, run_dir)
    demo = _path(root, demo_dir)
    files = []
    used_paths = {"bundle.json"}

    def add_file(relative: str, artifact: dict | None = None) -> Path:
        path = _path(root, relative)
        if relative.casefold() in used_paths:
            raise ValueError(f"Colliding bundle path: {relative}")
        if artifact is not None:
            verify_artifact(root, artifact)
        files.append(_record(root, path))
        used_paths.add(relative.casefold())
        return path

    # Preserve the trusted run manifest rather than changing its artifact hashes.
    manifest_path = add_file(f"{run_dir}/run_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    model_dir = manifest["model_dir"]
    _path(root, model_dir)
    required = [
        f"{model_dir}/any_rejection_selected_model.joblib",
        f"{run_dir}/any_rejection_frozen.json",
        f"{run_dir}/biopsy_results.json",
    ]
    artifacts = {item["file"]: item for item in manifest["artifacts"]}
    if len(artifacts) != len(manifest["artifacts"]):
        raise ValueError("Training manifest contains duplicate artifact paths.")
    for relative in required:
        if relative not in artifacts:
            raise ValueError(f"Required container artifact is missing: {relative}")
        add_file(relative, artifacts[relative])
    predictor = load_predictor(root, run_dir)

    frozen = json.loads((run / "any_rejection_frozen.json").read_text(encoding="utf-8"))
    results = json.loads((run / "biopsy_results.json").read_text(encoding="utf-8"))["any_rejection"]
    if results["selected_model"] != frozen["selected_model"]:
        raise ValueError("Evaluation results name a different selected model.")
    metrics = results["author_validation"][results["selected_model"]]
    required_metrics = {"n", "positives", "fn", "fp", "tp", "tn", "sensitivity", "specificity"}
    if not required_metrics.issubset(metrics) or metrics["threshold"] != predictor.threshold:
        raise ValueError("Evaluation results do not match the frozen model threshold.")

    demo_manifest_path = add_file(f"{demo_dir}/manifest.json")
    demo_manifest = json.loads(demo_manifest_path.read_text(encoding="utf-8"))
    if (
        demo_manifest["run_dir"] != run_dir
        or demo_manifest["model_version"] != predictor.model_version
    ):
        raise ValueError("Demo examples were prepared for a different run or model.")
    ids = set()
    validity_labels = set()
    for example in demo_manifest["examples"]:
        ident = example["id"]
        if (
            not isinstance(ident, str)
            or not re.fullmatch(r"[a-z0-9-]{1,40}", ident)
            or ident in ids
        ):
            raise ValueError("Demo example IDs must be valid and unique.")
        ids.add(ident)
        if not all(
            isinstance(example[key], str) and example[key].strip()
            for key in ("label", "description")
        ) or not isinstance(example["valid"], bool):
            raise ValueError("Demo examples need descriptions and boolean validity labels.")
        path = add_file(example["file"], example)
        if path.parent != demo or path.suffix != ".csv" or path.stat().st_size > MAX_UPLOAD_BYTES:
            raise ValueError("Demo example must be a small CSV inside the selected demo directory.")
        try:
            counts = read_counts_csv(path, predictor.schema, max_specimens=MAX_SPECIMENS)
        except ValueError:
            if example["valid"]:
                raise ValueError(f"Demo example marked valid fails input checks: {ident}") from None
        else:
            if not example["valid"]:
                raise ValueError(f"Demo example marked invalid passes input checks: {ident}")
            predictor.predict(counts)
        validity_labels.add(example["valid"])
    if validity_labels != {True, False}:
        raise ValueError("Container demo needs both a valid and an invalid example.")

    # Verify everything before creating output; verify copied bytes as well.
    output.mkdir(parents=True)
    for item in files:
        destination = project_path(output, item["file"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project_path(root, item["file"]), destination)
        verify_artifact(output, item)
    load_predictor(output, run_dir)
    bundle = {
        "bundle_version": 1,
        "run_dir": run_dir,
        "demo_dir": demo_dir,
        "model_version": predictor.model_version,
        "schema_version": predictor.schema.schema_version,
        "files": files,
    }
    # This completion record is written last, so an interrupted copy is not ready.
    (output / "bundle.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    return bundle


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--results-dir", default="results/reproduction/20260915_shared")
    parser.add_argument("--demo-dir", default="data/demo")
    parser.add_argument("--output-dir", default="build/container")
    args = parser.parse_args(argv)
    try:
        bundle = prepare_bundle(args.project_root, args.results_dir, args.demo_dir, args.output_dir)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(f"Prepared {len(bundle['files'])} files in {args.output_dir}")
    print(f"Model: {bundle['model_version']}")


if __name__ == "__main__":
    main()
