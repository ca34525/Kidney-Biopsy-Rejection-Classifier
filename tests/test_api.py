"""API/CLI agreement, complete-batch validation, and trusted-artifact readiness."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import joblib
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from pandas.testing import assert_frame_equal
from sklearn.linear_model import LogisticRegression

from kidney_biopsy.api import MAX_SPECIMENS, MAX_UPLOAD_BYTES, create_app
from kidney_biopsy.cli import main as predict_main
from kidney_biopsy.prediction import load_predictor, sha256
from kidney_biopsy.preprocessing import HOUSEKEEPING_TARGETS, AssaySchema, normalize_counts


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / "results/test"
        self.run.mkdir(parents=True)
        model_dir = self.root / "data/models"
        model_dir.mkdir(parents=True)
        self.raw = pd.DataFrame(
            {
                "IFNG": [0.0, 10.0, 50.0, 100.0],
                "CXCL9": [1.0, 8.0, 80.0, 90.0],
                **{target: [1.0, 2.0, 3.0, 4.0] for target in HOUSEKEEPING_TARGETS},
            },
            index=["001", "002", "003", "004"],
        )
        self.schema = AssaySchema(("IFNG", "CXCL9"))
        fitted = LogisticRegression().fit(normalize_counts(self.raw, self.schema), [0, 0, 1, 1])
        self.model_path = model_dir / "any_rejection_selected_model.joblib"
        joblib.dump(fitted, self.model_path)
        self.frozen_path = self.run / "any_rejection_frozen.json"
        self.frozen = {
            "features": list(self.schema.features),
            "schema": self.schema.to_dict(),
            "threshold": 0.61,
            "target": "any_rejection",
            "selected_model": "logistic",
            "model_version": "synthetic-test-v1",
        }
        self.write_manifest()
        self.app = create_app(project_root=self.root, run_dir="results/test")
        self.client = self.enterContext(TestClient(self.app))

    def write_manifest(self):
        self.frozen_path.write_text(json.dumps(self.frozen), encoding="utf-8")
        artifacts = [
            {
                "file": path.relative_to(self.root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in (self.model_path, self.frozen_path)
        ]
        (self.run / "run_manifest.json").write_text(
            json.dumps({"model_dir": "data/models", "artifacts": artifacts}), encoding="utf-8"
        )

    def post(self, frame):
        return self.client.post(
            "/predict",
            content=frame.to_csv(index_label="specimen"),
            headers={"Content-Type": "text/csv"},
        )

    def assert_invalid(self, response, status=422):
        self.assertEqual(response.status_code, status, response.text)
        self.assertEqual(set(response.json()), {"error"})
        self.assertEqual(set(response.json()["error"]), {"code", "message"})
        self.assertNotIn("Traceback", response.text)
        self.assertNotIn(str(self.root), response.text)

    def test_api_cli_and_direct_scores_agree_with_reordered_columns(self):
        self.raw.to_csv(self.root / "counts.csv", index_label="specimen")
        with redirect_stdout(io.StringIO()):
            predict_main(
                [
                    "--project-root",
                    str(self.root),
                    "--results-dir",
                    "results/test",
                    "--counts-csv",
                    "counts.csv",
                    "--output",
                    "cli.csv",
                ]
            )
        before_files = sorted(
            path.relative_to(self.root) for path in self.root.rglob("*") if path.is_file()
        )
        response = self.post(self.raw.iloc[:, ::-1])
        self.assertEqual(response.status_code, 200, response.text)
        actual = pd.DataFrame(response.json()["predictions"])
        expected = pd.read_csv(self.root / "cli.csv", dtype={"specimen": str})
        assert_frame_equal(actual, expected, atol=1e-12, rtol=0)
        assert_frame_equal(
            actual, load_predictor(self.root, "results/test").predict(self.raw), atol=1e-12, rtol=0
        )
        self.assertEqual(actual.rejection_flag.tolist(), (actual.rejection_score >= 0.61).tolist())
        self.assertEqual(response.json()["input_checks"]["specimens"], 4)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(
            sorted(path.relative_to(self.root) for path in self.root.rglob("*") if path.is_file()),
            before_files,
        )

    def test_missing_duplicate_or_extra_targets_fail_entire_batch(self):
        duplicate = pd.concat([self.raw, self.raw[["IFNG"]]], axis=1)
        for data in [
            self.raw.drop(columns="IFNG"),
            self.raw.drop(columns=HOUSEKEEPING_TARGETS[0]),
            duplicate,
            self.raw.assign(private_metadata="private-value"),
        ]:
            with self.subTest(columns=list(data.columns)):
                response = self.post(data)
                self.assert_invalid(response)
                self.assertNotIn("private_metadata", response.text)
                self.assertNotIn("private-value", response.text)

    def test_one_invalid_count_rejects_every_specimen_without_echoing_data(self):
        for value in ["private-count-value", "", -1.0, np.nan, np.inf]:
            frame = self.raw.astype(object)
            frame.loc["004", "IFNG"] = value
            frame.index = ["private-specimen-id", "002", "003", "004"]
            with self.subTest(value=value):
                response = self.post(frame)
                self.assert_invalid(response)
                self.assertNotIn("private-count-value", response.text)
                self.assertNotIn("private-specimen-id", response.text)

    def test_missing_and_duplicate_specimen_ids_fail(self):
        for labels in [["same", "same", "a", "b"], ["", "a", "b", "c"]]:
            with self.subTest(labels=labels):
                self.assert_invalid(self.post(self.raw.set_axis(labels)))

    def test_empty_ragged_quoted_and_non_utf8_csv_fail_clearly(self):
        for body in [
            b"",
            b"specimen,IFNG\n",
            b"specimen,IFNG\na,1,2\n",
            b'specimen,IFNG\n"unclosed,2',
            b"\xff\xfe",
        ]:
            with self.subTest(body=body):
                self.assert_invalid(
                    self.client.post("/predict", content=body, headers={"Content-Type": "text/csv"})
                )

    def test_batch_limit_is_applied_before_returning_results(self):
        frame = pd.concat([self.raw.iloc[[0]]] * (MAX_SPECIMENS + 1)).set_axis(
            [str(i) for i in range(MAX_SPECIMENS + 1)]
        )
        response = self.post(frame)
        self.assert_invalid(response)
        self.assertIn("16-specimen", response.json()["error"]["message"])

    def test_body_size_limit_checks_announced_and_actual_bytes(self):
        body = b"a" * (MAX_UPLOAD_BYTES + 1)
        for headers in [
            {"Content-Type": "text/csv"},
            {"Content-Type": "text/csv", "Content-Length": "1"},
        ]:
            with self.subTest(headers=headers):
                response = self.client.post("/predict", content=body, headers=headers)
                self.assert_invalid(response, 413)
        # Streaming request has no Content-Length; the byte limit still applies.
        request = self.client.build_request(
            "POST",
            "/predict",
            content=iter([body[:100], body[100:]]),
            headers={"Content-Type": "text/csv"},
        )
        self.assertNotIn("content-length", request.headers)
        self.assert_invalid(self.client.send(request), 413)

    def test_wrong_media_encoding_and_content_length_fail(self):
        for headers, status in [
            ({"Content-Type": "application/json"}, 415),
            ({"Content-Type": "text/csv", "Content-Encoding": "gzip"}, 415),
            ({"Content-Type": "text/csv", "Content-Length": "not-an-integer"}, 400),
            ({"Content-Type": "text/csv", "Content-Length": "-1"}, 400),
        ]:
            with self.subTest(headers=headers):
                self.assert_invalid(
                    self.client.post("/predict", content=b"counts", headers=headers), status
                )

    def test_model_is_loaded_once_and_caller_cannot_select_an_artifact(self):
        with patch("kidney_biopsy.api.load_predictor", wraps=load_predictor) as loader:
            with TestClient(create_app(project_root=self.root, run_dir="results/test")) as client:
                self.assertEqual(
                    client.get("/health").json(), {"status": "ready", "model_loaded": True}
                )
                schema = client.get("/model").json()
                self.assertEqual(schema["required_targets"], list(self.schema.required_targets))
                self.assertEqual(schema["threshold"], 0.61)
                response = client.post(
                    "/predict?model_dir=uploaded-model",
                    content=self.raw.to_csv(index_label="specimen"),
                    headers={"Content-Type": "text/csv"},
                )
                self.assert_invalid(response, 400)
                loader.assert_called_once_with(self.root, "results/test")

    def test_missing_corrupted_and_schema_incompatible_models_are_unready(self):
        for problem in ["missing", "corrupt", "schema"]:
            with self.subTest(problem=problem):
                if problem == "missing":
                    run_dir = "results/missing"
                elif problem == "corrupt":
                    run_dir = "results/test"
                    original = self.model_path.read_bytes()
                    self.model_path.write_bytes(original + b"changed")
                else:
                    self.model_path.write_bytes(original)
                    self.frozen["schema"]["schema_version"] = "incompatible-v99"
                    self.write_manifest()
                with TestClient(create_app(project_root=self.root, run_dir=run_dir)) as client:
                    health = client.get("/health")
                    self.assertEqual(health.status_code, 503)
                    self.assertFalse(health.json()["model_loaded"])
                    self.assert_invalid(client.get("/model"), 503)
                    self.assert_invalid(client.post("/predict", content=b"anything"), 503)
                    self.assertEqual(client.get("/").status_code, 200)

    def test_unexpected_prediction_failure_has_no_partial_results_or_internal_details(self):
        with patch.object(
            self.app.state.predictor.model,
            "predict_proba",
            side_effect=RuntimeError("private internal values"),
        ):
            response = self.post(self.raw)
        self.assert_invalid(response, 503)
        self.assertNotIn("private internal values", response.text)

    def test_optional_examples_are_allowlisted_and_checked_before_serving(self):
        self.assertEqual(self.client.get("/demo/examples").json(), {"examples": []})
        self.assert_invalid(self.client.get("/demo/examples/not-an-allowed-file"), 404)
        demo = self.root / "data/demo"
        demo.mkdir(parents=True)
        path = demo / "valid.csv"
        self.raw.iloc[[0]].to_csv(path, index_label="specimen")
        item = {
            "id": "valid",
            "label": "Synthetic example",
            "description": "Test fixture",
            "valid": True,
            "file": "data/demo/valid.csv",
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        (demo / "manifest.json").write_text(json.dumps({"examples": [item]}), encoding="utf-8")
        with TestClient(create_app(project_root=self.root, run_dir="results/test")) as client:
            self.assertEqual(client.get("/demo/examples").json()["examples"][0]["id"], "valid")
            response = client.get("/demo/examples/valid")
            self.assertEqual(response.content, path.read_bytes())
            path.write_text("changed", encoding="utf-8")
            self.assert_invalid(client.get("/demo/examples/valid"), 503)

    def test_malformed_optional_examples_do_not_break_upload_predictions(self):
        demo = self.root / "data/demo"
        demo.mkdir(parents=True)
        path = demo / "valid.csv"
        self.raw.iloc[[0]].to_csv(path, index_label="specimen")
        item = {
            "id": "valid",
            "label": "Synthetic example",
            "description": "Test fixture",
            "valid": True,
            "file": "data/demo/valid.csv",
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for field, value in [("label", None), ("description", []), ("valid", "false")]:
            malformed = {**item, field: value}
            if value is None:
                del malformed[field]
            with self.subTest(field=field):
                (demo / "manifest.json").write_text(
                    json.dumps({"examples": [malformed]}), encoding="utf-8"
                )
                with TestClient(
                    create_app(project_root=self.root, run_dir="results/test")
                ) as client:
                    self.assertEqual(client.get("/health").status_code, 200)
                    self.assertEqual(client.get("/demo/examples").json(), {"examples": []})
                    response = client.post(
                        "/predict",
                        content=self.raw.to_csv(index_label="specimen"),
                        headers={"Content-Type": "text/csv"},
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(len(response.json()["predictions"]), len(self.raw))

    def prepare_walkthrough(self, frame=None, **overrides):
        demo = self.root / "data/demo"
        demo.mkdir(parents=True, exist_ok=True)
        path = demo / "valid.csv"
        (self.raw.iloc[[0]] if frame is None else frame).to_csv(path, index_label="specimen")
        item = {
            "id": "valid",
            "label": "Synthetic example",
            "description": "Test fixture",
            "valid": True,
            "specimen": "001",
            "recorded_diagnosis": "No Rejection",
            "file": "data/demo/valid.csv",
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            **overrides,
        }
        (demo / "manifest.json").write_text(
            json.dumps({"examples": [item], "model_version": self.frozen["model_version"]}),
            encoding="utf-8",
        )
        return path

    def test_public_walkthrough_matches_raw_prediction_and_shared_normalization(self):
        frame = self.raw.iloc[[0], ::-1]
        # Use unequal housekeeping counts so the test can detect an average taken
        # on raw counts instead of the specified mean of logged counts.
        frame = frame.copy()
        frame.loc["001", HOUSEKEEPING_TARGETS[0]] = 255.0
        self.prepare_walkthrough(frame)
        with TestClient(create_app(project_root=self.root, run_dir="results/test")) as client:
            response = client.get("/demo/walkthrough/valid")
            self.assertEqual(response.status_code, 200, response.text)
            walkthrough = response.json()
            prediction = client.post(
                "/predict",
                content=frame.to_csv(index_label="specimen"),
                headers={"Content-Type": "text/csv"},
            ).json()["predictions"][0]
            self.assertEqual(walkthrough["prediction"], prediction)
            self.assertEqual(walkthrough["recorded_diagnosis"], "No Rejection")
            self.assertFalse(walkthrough["recorded_rejection"])
            self.assertEqual(walkthrough["model_version"], prediction["model_version"])
            self.assertEqual(walkthrough["schema_version"], prediction["schema_version"])
            values = walkthrough["normalization"]
            self.assertEqual(values["raw_count"], 0)
            self.assertEqual(len(values["housekeeping"]), 12)
            self.assertAlmostEqual(values["housekeeping_mean"], (8 + 11) / 12)
            self.assertAlmostEqual(
                values["normalized_value"], normalize_counts(frame, self.schema).loc["001", "IFNG"]
            )
            self.assertEqual(walkthrough["predictor_targets"], len(self.schema.features))
            self.assertEqual(response.headers["cache-control"], "no-store")

    def test_walkthrough_refuses_changed_files_invalid_labels_and_wrong_specimens(self):
        for changes in [
            {"specimen": "another-specimen"},
            {"recorded_diagnosis": "Unknown diagnosis"},
            {"recorded_diagnosis": None},
        ]:
            with self.subTest(changes=changes):
                self.prepare_walkthrough(**changes)
                with TestClient(
                    create_app(project_root=self.root, run_dir="results/test")
                ) as client:
                    self.assert_invalid(client.get("/demo/walkthrough/valid"), 503)
                    self.assertEqual(client.get("/health").status_code, 200)
        path = self.prepare_walkthrough()
        with TestClient(create_app(project_root=self.root, run_dir="results/test")) as client:
            path.write_text("changed", encoding="utf-8")
            self.assert_invalid(client.get("/demo/walkthrough/valid"), 503)

    def test_walkthrough_is_only_available_for_one_valid_prepared_public_specimen(self):
        self.prepare_walkthrough(self.raw)
        with TestClient(create_app(project_root=self.root, run_dir="results/test")) as client:
            self.assert_invalid(client.get("/demo/walkthrough/valid"), 503)
            self.assert_invalid(client.get("/demo/walkthrough/private-upload.csv"), 404)
        self.prepare_walkthrough(valid=False)
        with TestClient(create_app(project_root=self.root, run_dir="results/test")) as client:
            self.assert_invalid(client.get("/demo/walkthrough/valid"), 404)

    def test_changed_model_hides_walkthrough_but_keeps_counts_and_predictions_available(self):
        self.prepare_walkthrough()
        self.frozen["model_version"] = "new-model-version"
        self.write_manifest()
        with TestClient(create_app(project_root=self.root, run_dir="results/test")) as client:
            self.assert_invalid(client.get("/demo/walkthrough/valid"), 503)
            self.assertEqual(client.get("/demo/examples/valid").status_code, 200)
            response = client.post(
                "/predict",
                content=self.raw.to_csv(index_label="specimen"),
                headers={"Content-Type": "text/csv"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json()["predictions"][0]["model_version"], "new-model-version"
            )

    def test_startup_logs_actionable_categories_without_private_exception_details(self):
        for exception, category in [
            (FileNotFoundError, "missing_artifact"),
            (ValueError, "invalid_artifact_or_schema"),
            (KeyError, "invalid_artifact_or_schema"),
            (PermissionError, "unreadable_artifact"),
            (RuntimeError, "unexpected_startup_error"),
        ]:
            with self.subTest(exception=exception):
                with (
                    patch(
                        "kidney_biopsy.api.load_predictor", side_effect=exception("private/path")
                    ),
                    self.assertLogs("kidney_biopsy.api", level="ERROR") as captured,
                    TestClient(
                        create_app(project_root=self.root, run_dir="results/test")
                    ) as client,
                ):
                    self.assertEqual(client.get("/health").status_code, 503)
                    self.assert_invalid(client.get("/demo/walkthrough/valid"), 503)
                log = "\n".join(captured.output)
                self.assertIn(category, log)
                self.assertIn("Check the configured run", log)
                self.assertNotIn("private/path", log)
                self.assertNotIn("Traceback", log)


if __name__ == "__main__":
    unittest.main()
