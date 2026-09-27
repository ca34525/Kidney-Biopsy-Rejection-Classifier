"""Execute each notebook in a fresh local kernel; preserve a new run and HTML views."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from kidney_biopsy.prediction import project_path, sha256

ROOT = Path(__file__).resolve().parents[1]


def rewrite_html_links(html: str, output: Path) -> str:
    """Keep local references usable when HTML sits in a dated result directory."""
    from bs4 import BeautifulSoup

    document = BeautifulSoup(html, "html.parser")
    for link in document.find_all("a", href=True):
        parsed = urlsplit(link["href"])
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        if parsed.path.endswith(".ipynb") and "/" not in parsed.path:
            target = output / Path(parsed.path).with_suffix(".html")
        else:
            target = (ROOT / "notebooks" / parsed.path).resolve()
        relative = Path(os.path.relpath(target, output)).as_posix()
        link["href"] = relative + (f"#{parsed.fragment}" if parsed.fragment else "")
    return str(document)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    parser.add_argument("--output-dir", default=f"results/notebooks/{stamp}")
    parser.add_argument("--run-dir", default="results/reproduction/20260915_shared")
    args = parser.parse_args()
    output = project_path(ROOT, args.output_dir)
    if not output.is_relative_to(ROOT / "results/notebooks"):
        parser.error("Use a new directory under results/notebooks.")
    if output.exists():
        parser.error("Output already exists; choose a new directory to preserve completed runs.")
    project_path(ROOT, args.run_dir)
    if sys.version_info[:2] != (3, 12) or not Path(sys.prefix).resolve().is_relative_to(ROOT):
        parser.error("Use this project's Python 3.12 environment.")
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    import nbformat
    from jupyter_client import AsyncKernelManager
    from jupyter_client.kernelspec import KernelSpecManager
    from nbclient import NotebookClient
    from nbconvert import HTMLExporter

    output.mkdir(parents=True)
    # A project-local kernel spec avoids user-level kernel installation and stale Python paths.
    kernels = ROOT / ".uv-cache/notebook-kernels"
    spec = kernels / "kidney-biopsy"
    spec.mkdir(parents=True, exist_ok=True)
    (spec / "kernel.json").write_text(
        json.dumps(
            {
                "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                "display_name": "Kidney biopsy (project Python)",
                "language": "python",
            }
        ),
        encoding="utf-8",
    )
    runtime = ROOT / ".uv-cache/jupyter-runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        "KIDNEY_BIOPSY_NOTEBOOK_RUN": args.run_dir,
        "KIDNEY_BIOPSY_NOTEBOOK_OUTPUT": args.output_dir,
        "JUPYTER_RUNTIME_DIR": str(runtime),
        "MPLCONFIGDIR": str(ROOT / ".uv-cache/matplotlib"),
        "IPYTHONDIR": str(ROOT / ".uv-cache/ipython"),
    }
    record = {"run_dir": args.run_dir, "successful": False, "notebooks": []}
    try:
        for path in sorted((ROOT / "notebooks").glob("[0-9][0-9]_*.ipynb")):
            started = time.perf_counter()
            print(f"Executing {path.name}", flush=True)
            notebook = nbformat.read(path, as_version=4)
            source_dir = output / "source"
            source_dir.mkdir(exist_ok=True)
            (source_dir / path.name).write_bytes(path.read_bytes())
            for cell in notebook.cells:
                if cell.cell_type == "code":
                    cell.outputs = []
                    cell.execution_count = None
            manager = AsyncKernelManager(
                kernel_name="kidney-biopsy",
                kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernels)]),
            )
            client = NotebookClient(
                notebook,
                km=manager,
                timeout=300,
                allow_errors=False,
                resources={"metadata": {"path": str(ROOT)}},
            )
            try:
                client.execute(env=env, cwd=str(ROOT))
            finally:
                if manager.has_kernel:
                    asyncio.run(manager.shutdown_kernel(now=True))
            # Store portable Python metadata in deliverables.
            notebook.metadata.kernelspec = {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3",
            }
            nbformat.validate(notebook)
            executed = output / path.name
            nbformat.write(notebook, executed)
            html, _ = HTMLExporter(template_name="lab").from_notebook_node(notebook)
            html = rewrite_html_links(html, output)
            (output / f"{path.stem}.html").write_text(html, encoding="utf-8")
            record["notebooks"].append(
                {
                    "file": path.name,
                    "source_sha256": sha256(path),
                    "executed_sha256": sha256(executed),
                    "html_sha256": sha256(output / f"{path.stem}.html"),
                    "seconds": round(time.perf_counter() - started, 2),
                    "code_cells": sum(c.cell_type == "code" for c in notebook.cells),
                }
            )
            print(f"Finished {path.name} ({record['notebooks'][-1]['seconds']} s)", flush=True)
        record["successful"] = True
    finally:
        (output / "execution.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"Completed: {args.output_dir}")


if __name__ == "__main__":
    main()
