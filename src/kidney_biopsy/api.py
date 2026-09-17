"""Serve raw-count predictions and a small research demonstration.

The /predict route checks the HTTP request, reads a complete CSV batch, and calls
Predictor.predict. Models and optional examples come only from local settings.
"""

from __future__ import annotations

import io
import json
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from .prediction import Predictor, load_predictor, project_path, verify_artifact
from .preprocessing import read_counts_csv

DEFAULT_RUN = "results/reproduction/20260915_shared"
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_SPECIMENS = 16
STATIC_DIR = Path(__file__).with_name("static")


def failure(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        {"error": {"code": code, "message": message}},
        status_code=status,
    )


def create_app(
    *,
    project_root: str | Path | None = None,
    run_dir: str | None = None,
    demo_dir: str | None = None,
) -> FastAPI:
    """Configure trusted local artifacts in process settings, never in a request."""
    root = Path(project_root or os.environ.get("KIDNEY_BIOPSY_PROJECT_ROOT", ".")).resolve()
    selected_run = run_dir or os.environ.get("KIDNEY_BIOPSY_RESULTS_DIR", DEFAULT_RUN)
    selected_demo = demo_dir or os.environ.get("KIDNEY_BIOPSY_DEMO_DIR", "data/demo")

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.predictor = None
        application.state.evaluation = None
        application.state.examples = {}
        try:
            predictor = await run_in_threadpool(load_predictor, root, selected_run)
            application.state.predictor = predictor
            application.state.evaluation = _load_evaluation(root, selected_run, predictor)
            application.state.examples = _load_demo_examples(root, selected_demo)
        except Exception:
            # Readiness reports a safe error. No model paths or upload data enter logs.
            application.state.predictor = None
        yield
        application.state.predictor = None

    application = FastAPI(
        title="Kidney biopsy rejection research API",
        version="0.1.0",
        lifespan=lifespan,
        description="Classify recorded rejection from compatible raw B-HOT measurements.",
        docs_url=None,
        redoc_url=None,
    )
    application.state.predictor = None
    application.state.evaluation = None
    application.state.examples = {}

    @application.middleware("http")
    async def response_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @application.get("/health")
    def health():
        ready = application.state.predictor is not None
        return JSONResponse(
            {"status": "ready" if ready else "unavailable", "model_loaded": ready},
            status_code=200 if ready else 503,
        )

    @application.get("/model")
    def model():
        predictor = application.state.predictor
        if predictor is None:
            return failure(503, "model_unavailable", "The configured research model is not ready.")
        return {
            "target": predictor.target,
            "model_version": predictor.model_version,
            "schema_version": predictor.schema.schema_version,
            "preprocessing_version": predictor.schema.preprocessing_version,
            "required_targets": list(predictor.schema.required_targets),
            "housekeeping_targets": list(predictor.schema.housekeeping_targets),
            "threshold": predictor.threshold,
            "max_specimens": MAX_SPECIMENS,
            "max_upload_bytes": MAX_UPLOAD_BYTES,
            "extra_targets": "reject",
            "batch_policy": "all_or_nothing",
            "threshold_selection": (
                "Highest specificity retaining at least 90% of discovery-screen rejection cases."
            ),
            "score_interpretation": (
                "A model score, not a verified probability for an individual biopsy."
            ),
            "evaluation": application.state.evaluation,
        }

    @application.post(
        "/predict",
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {"text/csv": {"schema": {"type": "string"}}},
            }
        },
    )
    async def predict(request: Request):
        predictor = application.state.predictor
        if predictor is None:
            return failure(503, "model_unavailable", "The configured research model is not ready.")

        request_error = _check_upload_headers(request)
        if request_error is not None:
            return request_error

        # Check the actual streamed size as well as the announced Content-Length.
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > MAX_UPLOAD_BYTES:
                return failure(413, "upload_too_large", "CSV exceeds the 2 MiB upload limit.")
            body.extend(chunk)
        try:
            csv_text = body.decode("utf-8-sig")
        except UnicodeDecodeError:
            return failure(422, "invalid_csv", "CSV must use UTF-8 text encoding.")

        # The reader validates every specimen before the model sees this batch.
        try:
            counts = await run_in_threadpool(
                read_counts_csv,
                io.StringIO(csv_text),
                predictor.schema,
                max_specimens=MAX_SPECIMENS,
            )
        except ValueError as error:
            message = str(error)
            if message.startswith("Unexpected assay targets or metadata columns"):
                message = (
                    "Unexpected assay targets or metadata columns. "
                    "Include only the required targets listed by /model."
                )
            # Do not echo uploaded metadata; bound a long missing-target list.
            return failure(422, "invalid_csv", message[:700])

        try:
            predictions = await run_in_threadpool(predictor.predict, counts)
        except Exception:
            return failure(
                503,
                "prediction_unavailable",
                "The research model could not score this batch. No predictions were returned.",
            )
        return {
            "predictions": predictions.to_dict(orient="records"),
            "input_checks": {
                "status": "passed",
                "specimens": len(counts),
                "required_targets": len(predictor.schema.required_targets),
                "batch_policy": "all_or_nothing",
                "assay_origin": "caller_responsibility",
            },
        }

    @application.get("/demo/examples")
    def examples():
        public_fields = ("id", "label", "description", "valid")
        return {
            "examples": [
                {key: item[key] for key in public_fields}
                for item in application.state.examples.values()
            ]
        }

    @application.get("/demo/examples/{example_id}")
    def example(example_id: str):
        item = application.state.examples.get(example_id)
        if item is None:
            return failure(
                404, "example_unavailable", "That prepared public example is unavailable."
            )
        try:
            path = verify_artifact(root, item)
            body = path.read_bytes()
        except (OSError, ValueError):
            return failure(
                503,
                "example_unavailable",
                "This public example failed its file check. Prepare the examples again.",
            )
        return Response(
            body,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{example_id}.csv"'},
        )

    @application.get("/", include_in_schema=False)
    def page():
        return FileResponse(STATIC_DIR / "index.html")

    application.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")
    return application


def _check_upload_headers(request: Request) -> JSONResponse | None:
    """Return an error for an unsupported CSV request, or None when it can be read."""
    if request.query_params:
        return failure(
            400,
            "unexpected_parameters",
            "This route accepts only a CSV body; it has no query parameters.",
        )
    encoding = request.headers.get("content-encoding", "identity").lower()
    if encoding != "identity":
        return failure(415, "unsupported_encoding", "Send an uncompressed UTF-8 CSV body.")

    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type not in {"text/csv", "application/csv"}:
        return failure(415, "unsupported_media_type", "Send raw CSV with Content-Type: text/csv.")
    if "content-length" in request.headers:
        try:
            length = int(request.headers["content-length"])
        except ValueError:
            return failure(
                400, "invalid_content_length", "Content-Length must be a nonnegative integer."
            )
        if length < 0:
            return failure(
                400, "invalid_content_length", "Content-Length must be a nonnegative integer."
            )
        if length > MAX_UPLOAD_BYTES:
            return failure(413, "upload_too_large", "CSV exceeds the 2 MiB upload limit.")
    return None


def _load_evaluation(root: Path, run_dir: str, predictor: Predictor) -> dict | None:
    """Use only aggregate evidence recorded in this same trusted training run."""
    try:
        directory = project_path(root, run_dir)
        manifest = json.loads((directory / "run_manifest.json").read_text(encoding="utf-8"))
        relative = (directory / "biopsy_results.json").relative_to(root).as_posix()
        artifact = next(item for item in manifest["artifacts"] if item["file"] == relative)
        results_path = verify_artifact(root, artifact)
        results = json.loads(results_path.read_text(encoding="utf-8"))["any_rejection"]
        metrics = results["author_validation"][results["selected_model"]]
        if metrics["threshold"] != predictor.threshold:
            return None
        return {
            "cohort": "Authors' technical-validation cohort",
            "specimens": metrics["n"],
            "recorded_rejection": metrics["positives"],
            "recorded_no_rejection": metrics["n"] - metrics["positives"],
            "missed_rejection": metrics["fn"],
            "false_rejection_flags": metrics["fp"],
            "correct_rejection_flags": metrics["tp"],
            "correct_no_rejection": metrics["tn"],
            "sensitivity": metrics["sensitivity"],
            "specificity": metrics["specificity"],
            "source": relative,
        }
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        return None


def _load_demo_examples(root: Path, demo_dir: str) -> dict:
    """Load a finite, project-prepared allowlist; request paths never select files."""
    try:
        directory = project_path(root, demo_dir)
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        examples = {}
        for item in manifest["examples"]:
            example_id = item["id"]
            if not re.fullmatch(r"[a-z0-9-]{1,40}", example_id) or example_id in examples:
                raise ValueError("Invalid example manifest.")
            description_is_valid = all(
                isinstance(item[key], str) and item[key].strip() for key in ("label", "description")
            )
            if not description_is_valid or not isinstance(item["valid"], bool):
                raise ValueError("Invalid example description.")
            path = verify_artifact(root, item)
            if (
                path.parent != directory
                or path.suffix != ".csv"
                or path.stat().st_size > MAX_UPLOAD_BYTES
            ):
                raise ValueError("Invalid example location or size.")
            examples[example_id] = item
        return examples
    except (OSError, ValueError, KeyError, TypeError):
        return {}


app = create_app()
