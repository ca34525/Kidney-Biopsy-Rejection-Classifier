"""Exercise a real local HTTP server against all saved validation predictions.

Uses project-controlled raw inputs and model artifacts. Writes aggregate evidence
and keeps specimen outputs in ignored local data. The server is stopped on exit.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx
import numpy as np
import pandas as pd

from kidney_biopsy.prediction import load_predictor, project_path, sha256, verify_artifact
from kidney_biopsy.source import read_geo_matrix, read_rcc_archive

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default="results/reproduction/20260915_shared")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--case-dir", required=True)
    args = parser.parse_args()
    output_dir = project_path(ROOT, args.output_dir)
    case_dir = project_path(ROOT, args.case_dir)
    for path in (output_dir, case_dir):
        if path.exists():
            raise ValueError("Verification destinations must be new directories.")
    if not case_dir.is_relative_to(ROOT / "data/processed"):
        raise ValueError("Specimen outputs must stay under data/processed.")
    output_dir.mkdir(parents=True)
    case_dir.mkdir(parents=True)
    source_records = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8-sig"))
    for record in source_records:
        verify_artifact(ROOT, record)
    predictor = load_predictor(ROOT, args.run_dir)
    run_dir = project_path(ROOT, args.run_dir)
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    frozen = json.loads((run_dir / "any_rejection_frozen.json").read_text(encoding="utf-8"))
    expected_path = run_dir / f"any_rejection_{frozen['selected_model']}_test_predictions.csv"
    expected_relative = expected_path.relative_to(ROOT).as_posix()
    record = next(item for item in manifest["artifacts"] if item["file"] == expected_relative)
    verify_artifact(ROOT, record)
    expected = pd.read_csv(expected_path, dtype={"sample": str}).set_index("sample")
    raw_dir = ROOT / "data/raw/rejection_public"
    _, metadata = read_geo_matrix(raw_dir / "GSE212160_series_matrix.txt.gz")
    counts, _ = read_rcc_archive(raw_dir / "GSE212160_RAW.tar", specimen_ids=metadata.index)
    validation = metadata.index[metadata.cohort.eq("Validation cohort sample")]
    counts = counts.loc[validation]
    if set(counts.index) != set(expected.index) or not expected.index.is_unique:
        raise ValueError("Validation and saved prediction specimen sets differ.")
    expected = expected.loc[counts.index]
    cli_path = case_dir / "cli.csv"
    subprocess.run([
        sys.executable, "-m", "kidney_biopsy", "--project-root", str(ROOT),
        "--geo-validation", "--results-dir", args.run_dir,
        "--output", cli_path.relative_to(ROOT).as_posix(),
    ], cwd=ROOT, check=True, capture_output=True, text=True)
    cli = pd.read_csv(cli_path, dtype={"specimen": str}).set_index("specimen").loc[counts.index]
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    env = os.environ.copy()
    env["KIDNEY_BIOPSY_PROJECT_ROOT"] = str(ROOT)
    env["KIDNEY_BIOPSY_RESULTS_DIR"] = args.run_dir
    server = None
    checks = []
    with (case_dir / "server.log").open("w", encoding="utf-8") as log:
        try:
            server = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "kidney_biopsy.api:app",
                "--host", "127.0.0.1", "--port", str(port), "--no-access-log",
            ], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=30, trust_env=False) as client:
                deadline = time.monotonic() + 30
                while True:
                    if server.poll() is not None:
                        raise RuntimeError("Local HTTP server exited before readiness.")
                    try:
                        health = client.get("/health")
                        if health.status_code == 200:
                            break
                    except httpx.ConnectError:
                        pass
                    if time.monotonic() > deadline:
                        raise RuntimeError("Local HTTP server did not become ready.")
                    time.sleep(.2)
                checks.append("real_http_server_ready")
                model_response = client.get("/model")
                model_response.raise_for_status()
                if model_response.json()["model_version"] != predictor.model_version:
                    raise ValueError("HTTP model version differs from the configured model.")
                page = client.get("/")
                page.raise_for_status()
                if "text/html" not in page.headers["content-type"]:
                    raise ValueError("Demo page was not served as HTML.")
                checks.append("demo_page_served")
                batches = []
                for start in range(0, len(counts), 16):
                    # Reverse the columns to verify the HTTP path honors target names.
                    csv_text = counts.iloc[start:start + 16, ::-1].to_csv(index_label="specimen")
                    response = client.post("/predict", content=csv_text.encode(), headers={"Content-Type": "text/csv"})
                    response.raise_for_status()
                    batches.extend(response.json()["predictions"])
                actual = pd.DataFrame(batches).set_index("specimen")
                if not actual.index.is_unique or set(actual.index) != set(counts.index):
                    raise ValueError("HTTP predictions have missing or duplicate specimen IDs.")
                actual = actual.loc[counts.index]
                np.testing.assert_allclose(actual.rejection_score, cli.rejection_score, rtol=0, atol=1e-12)
                np.testing.assert_allclose(actual.rejection_score, expected.probability, rtol=0, atol=1e-12)
                np.testing.assert_array_equal(actual.rejection_flag, expected.predicted)
                np.testing.assert_array_equal(actual.rejection_flag, cli.rejection_flag)
                np.testing.assert_allclose(actual.threshold, predictor.threshold, rtol=0, atol=0)
                if set(actual.model_version) != {predictor.model_version} or set(actual.input_check) != {"passed"}:
                    raise ValueError("HTTP version or input checks differ across results.")
                checks.append("all_345_http_cli_saved_predictions_agree_with_reordered_columns")
                bad = counts.iloc[:2].drop(columns="IFNG").to_csv(index_label="specimen")
                invalid = client.post("/predict", content=bad.encode(), headers={"Content-Type": "text/csv"})
                if invalid.status_code != 422 or "error" not in invalid.json() or "predictions" in invalid.json():
                    raise ValueError("Invalid HTTP input did not fail as a whole with a structured error.")
                checks.append("invalid_http_batch_rejected_without_predictions")
                oversize_batch = client.post("/predict", content=counts.iloc[:17].to_csv(index_label="specimen").encode(),
                                            headers={"Content-Type": "text/csv"})
                if oversize_batch.status_code not in (413, 422) or "predictions" in oversize_batch.json():
                    raise ValueError("HTTP specimen batch limit was not enforced.")
                checks.append("http_batch_limit_enforced")
                actual.to_csv(case_dir / "http.csv", index_label="specimen")
        finally:
            if server is not None:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=10)
    summary = {
        "verified_utc": datetime.now(timezone.utc).isoformat(), "successful": True,
        "run_dir": args.run_dir, "model_version": predictor.model_version,
        "run_manifest_sha256": sha256(run_dir / "run_manifest.json"),
        "specimens": len(actual), "http_requests_for_predictions": (len(actual) + 15) // 16,
        "numeric_tolerance": 1e-12,
        "max_http_cli_score_difference": float(np.max(np.abs(actual.rejection_score - cli.rejection_score))),
        "max_http_saved_score_difference": float(np.max(np.abs(actual.rejection_score - expected.probability))),
        "checks": checks, "script_sha256": sha256(Path(__file__)),
        "source_hashes": {path.relative_to(ROOT).as_posix(): sha256(path)
                          for path in sorted((ROOT / "src/kidney_biopsy").rglob("*"))
                          if path.is_file() and path.suffix in {".py", ".html", ".css", ".js"}},
        "case_directory": args.case_dir,
    }
    (output_dir / "http.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
