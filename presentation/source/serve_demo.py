"""Serve the presentation files beside the unchanged research application."""

import argparse
from pathlib import Path

import uvicorn
from fastapi.staticfiles import StaticFiles

from kidney_biopsy.api import create_app

ROOT = Path(__file__).resolve().parents[2]


def presentation_app():
    app = create_app(project_root=ROOT)
    app.mount("/presentation", StaticFiles(directory=ROOT / "presentation"), name="presentation")
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    print(
        f"Engineering demonstration: http://127.0.0.1:{args.port}/presentation/engineering_demo.html",
        flush=True,
    )
    uvicorn.run(presentation_app(), host="127.0.0.1", port=args.port, access_log=False)


if __name__ == "__main__":
    main()
