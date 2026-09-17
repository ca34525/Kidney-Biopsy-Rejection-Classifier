"""Check a container or deployed URL against its trusted local serving bundle.

With --image, start a temporary Docker container and remove it on exit. With
--url, check an already running service. Only aggregate evidence is recorded.
"""

from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from kidney_biopsy.prediction import load_predictor, project_path, sha256, verify_artifact
from kidney_biopsy.preprocessing import read_counts_csv

ROOT = Path(__file__).resolve().parents[1]


def check_service(client, bundle_root: Path, bundle: dict) -> dict:
    """Compare every prepared example through HTTP and the local predictor."""
    predictor = load_predictor(bundle_root, bundle["run_dir"])
    model_response = client.get("/model")
    model_response.raise_for_status()
    model = model_response.json()
    if (
        model["model_version"] != predictor.model_version
        or model["schema_version"] != predictor.schema.schema_version
        or model["threshold"] != predictor.threshold
        or model["required_targets"] != list(predictor.schema.required_targets)
    ):
        raise ValueError("Service model or schema differs from the local bundle.")

    results_path = project_path(bundle_root, bundle["run_dir"]) / "biopsy_results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))["any_rejection"]
    metrics = results["author_validation"][results["selected_model"]]
    expected_evaluation = {
        "specimens": metrics["n"],
        "recorded_rejection": metrics["positives"],
        "recorded_no_rejection": metrics["n"] - metrics["positives"],
        "missed_rejection": metrics["fn"],
        "false_rejection_flags": metrics["fp"],
        "correct_rejection_flags": metrics["tp"],
        "correct_no_rejection": metrics["tn"],
        "sensitivity": metrics["sensitivity"],
        "specificity": metrics["specificity"],
    }
    evaluation = model.get("evaluation") or {}
    if any(evaluation.get(key) != value for key, value in expected_evaluation.items()):
        raise ValueError("Displayed evaluation counts differ from the prepared run.")

    for route, content_type in (
        ("/", "text/html"),
        ("/assets/style.css", "text/css"),
        ("/assets/app.js", "javascript"),
    ):
        response = client.get(route)
        response.raise_for_status()
        if not response.content or content_type not in response.headers["content-type"]:
            raise ValueError(f"Missing or incorrect packaged page asset: {route}")

    demo_path = project_path(bundle_root, bundle["demo_dir"]) / "manifest.json"
    examples = json.loads(demo_path.read_text(encoding="utf-8"))["examples"]
    listing = client.get("/demo/examples")
    listing.raise_for_status()
    if listing.json()["examples"] != [
        {key: item[key] for key in ("id", "label", "description", "valid")} for item in examples
    ]:
        raise ValueError("Service example listing differs from the prepared bundle.")

    valid_count = invalid_count = 0
    largest_difference = 0.0
    for item in examples:
        expected_bytes = verify_artifact(bundle_root, item).read_bytes()
        downloaded = client.get(f"/demo/examples/{item['id']}")
        downloaded.raise_for_status()
        if downloaded.content != expected_bytes:
            raise ValueError("Served example differs from its prepared CSV.")
        body = expected_bytes
        if item["valid"]:
            counts = read_counts_csv(io.StringIO(body.decode("utf-8")), predictor.schema)
            # Column order may change in a user's file; match targets by name.
            body = counts.iloc[:, ::-1].to_csv(index_label="specimen").encode("utf-8")
        response = client.post("/predict", content=body, headers={"Content-Type": "text/csv"})
        if item["valid"]:
            response.raise_for_status()
            expected = predictor.predict(counts)
            actual = pd.DataFrame(response.json()["predictions"])
            assert_frame_equal(actual, expected, atol=1e-12, rtol=0)
            difference = np.max(np.abs(actual.rejection_score - expected.rejection_score))
            largest_difference = max(largest_difference, float(difference))
            valid_count += len(counts)
        else:
            payload = response.json()
            if (
                response.status_code != 422
                or set(payload) != {"error"}
                or payload["error"]["code"] != "invalid_csv"
                or "Traceback" in response.text
            ):
                raise ValueError("Invalid example did not produce a structured rejection.")
            invalid_count += 1
    if not valid_count or not invalid_count:
        raise ValueError("Verification requires both valid and invalid prepared examples.")
    return {
        "model_version": predictor.model_version,
        "schema_version": predictor.schema.schema_version,
        "valid_specimens": valid_count,
        "invalid_examples_rejected": invalid_count,
        "maximum_score_difference": largest_difference,
        "score_tolerance": 1e-12,
        "flags_and_metadata_agree": True,
        "page_and_assets_served": True,
        "example_files_agree": True,
        "evaluation_counts_agree": True,
    }


def wait_for_readiness(client, timeout: float = 60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            response = client.get("/health")
            if response.status_code == 200 and response.json() == {
                "status": "ready",
                "model_loaded": True,
            }:
                return
        except httpx.TransportError:
            pass
        time.sleep(0.5)
    raise RuntimeError("Service did not become ready within 60 seconds.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--image", help="Local Docker image to start and check.")
    target.add_argument("--url", help="Existing local or HTTPS service URL to check.")
    parser.add_argument("--bundle-dir", default="build/container")
    parser.add_argument("--output", required=True, help="New project-relative JSON record.")
    parser.add_argument("--docker", default="docker", help="Docker executable, if not on PATH.")
    args = parser.parse_args()
    output = project_path(ROOT, args.output)
    if output.exists():
        raise ValueError("Check record already exists; choose a new --output path.")
    bundle_root = project_path(ROOT, args.bundle_dir)
    record = {
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "successful": False,
        "verification": "docker" if args.image else "existing_url",
        "errors": [],
    }
    container_name = "kidney-biopsy-check-" + uuid.uuid4().hex[:12]
    started = time.perf_counter()
    container_started = False

    def docker(*arguments):
        return subprocess.run(
            [args.docker, *arguments],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        ).stdout.strip()

    try:
        bundle = json.loads((bundle_root / "bundle.json").read_text(encoding="utf-8"))
        if bundle["bundle_version"] != 1:
            raise ValueError("Unsupported bundle version.")
        for item in bundle["files"]:
            verify_artifact(bundle_root, item)
        record["bundle_sha256"] = sha256(bundle_root / "bundle.json")
        url = args.url
        if args.image:
            if not shutil.which(args.docker):
                raise RuntimeError("Docker is unavailable; install/start Docker Desktop first.")
            info = json.loads(docker("image", "inspect", args.image))[0]
            user = info["Config"]["User"]
            if not user or user.split(":")[0] in {"0", "root"}:
                raise ValueError("Container image must configure a non-root user.")
            record["image"] = {
                "tag": args.image,
                "id": info["Id"],
                "bytes": info["Size"],
                "user": user,
            }
            docker(
                "create",
                "--name",
                container_name,
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--publish",
                "127.0.0.1::8000",
                args.image,
            )
            container_started = True
            docker("start", container_name)
            binding = docker("port", container_name, "8000/tcp")
            url = "http://" + binding
        with httpx.Client(base_url=url.rstrip("/"), timeout=10, trust_env=False) as client:
            wait_for_readiness(client)
            record["checks"] = check_service(client, bundle_root, bundle)
        if args.image:
            # Run the image's own readiness command as well as the external HTTP check.
            health_command = info["Config"]["Healthcheck"]["Test"]
            if health_command[0] != "CMD":
                raise ValueError("Expected an explicit container readiness command.")
            docker("exec", container_name, *health_command[1:])
            record["checks"]["docker_healthcheck_passed"] = True
            record["checks"]["read_only_container"] = True
        record["successful"] = True
    except Exception as error:
        # Retain the exception summary, without copying Docker stdout/stderr.
        record["errors"].append(f"{type(error).__name__}: {error}")
    finally:
        if container_started:
            try:
                docker("rm", "--force", container_name)
            except Exception as error:
                record["successful"] = False
                record["errors"].append(f"Container cleanup failed: {error}")
        record["elapsed_seconds"] = round(time.perf_counter() - started, 3)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2)
            stream.write("\n")
    print(f"{'PASS' if record['successful'] else 'FAIL'}: {args.output}")
    if not record["successful"]:
        for error in record["errors"]:
            print(error)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
