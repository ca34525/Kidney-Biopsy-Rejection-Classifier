"""Serve the presentation files beside the unchanged research application."""

import argparse
import json
from pathlib import Path

import uvicorn
from fastapi.staticfiles import StaticFiles

from kidney_biopsy.api import create_app
from kidney_biopsy.prediction import load_predictor, project_path, verify_artifact

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / "presentation/source/demo_config.json").read_text(encoding="utf-8"))


def presentation_app(*, project_root=ROOT, run_dir=None, demo_dir=None):
    root = Path(project_root).resolve()
    if (run_dir is None) != (demo_dir is None):
        raise ValueError("Select both --run-dir and --demo-dir so examples match the model.")
    run_dir = CONFIG["run_dir"] if run_dir is None else run_dir
    demo_dir = CONFIG["demo_dir"] if demo_dir is None else demo_dir
    # Fail before opening a port if this checkout lacks the selected local files.
    predictor = load_predictor(root, run_dir)
    examples = json.loads((project_path(root, demo_dir) / "manifest.json").read_text("utf-8"))
    if examples["run_dir"] != run_dir or examples["model_version"] != predictor.model_version:
        raise ValueError("Prepared examples belong to a different run; prepare matching examples.")
    if not examples["examples"]:
        raise ValueError("The presentation needs prepared public examples.")
    for example in examples["examples"]:
        verify_artifact(root, example)
    app = create_app(project_root=root, run_dir=run_dir, demo_dir=demo_dir)
    app.mount("/presentation", StaticFiles(directory=root / "presentation"), name="presentation")
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=CONFIG["port"])
    parser.add_argument(
        "--run-dir", help="Completed project-relative run; defaults to demo_config.json."
    )
    parser.add_argument("--demo-dir", help="Matching prepared examples; required with --run-dir.")
    args = parser.parse_args()
    try:
        app = presentation_app(run_dir=args.run_dir, demo_dir=args.demo_dir)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(
            1,
            f"Demo setup failed: {error}\n"
            "Models and examples are local files, not included in Git. See docs/SETUP.md.\n"
            "Select an available run with --run-dir and matching --demo-dir; "
            "the launcher does not train or substitute a model.\n",
        )
    print(f"Configured run: {args.run_dir or CONFIG['run_dir']}", flush=True)
    print(
        f"Engineering demonstration: http://127.0.0.1:{args.port}/presentation/engineering_demo.html",
        flush=True,
    )
    uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False)


if __name__ == "__main__":
    main()
