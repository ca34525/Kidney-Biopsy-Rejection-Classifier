"""Exercise portable launch settings and preserve the saved presentation evidence."""

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from presentation.source.check_demo import check_reference, check_response
from presentation.source.serve_demo import presentation_app
from scripts.prepare_ci_fixture import prepare_fixture


class PresentationLaunchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="kidney demo ")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name) / "project with spaces"
        prepare_fixture(cls.root)
        (cls.root / "presentation").mkdir()
        (cls.root / "presentation/engineering_demo.html").write_text("Demo", encoding="utf-8")

    def test_explicit_run_serves_matching_model_examples_and_presentation(self):
        app = presentation_app(project_root=self.root, run_dir="results/ci", demo_dir="data/demo")
        with TestClient(app) as client:
            self.assertEqual(client.get("/health").status_code, 200)
            self.assertEqual(client.get("/model").json()["model_version"], "synthetic-ci-only")
            self.assertEqual(client.get("/presentation/engineering_demo.html").text, "Demo")
            valid = client.get("/demo/examples/valid")
            self.assertEqual(valid.status_code, 200)
            response = client.post(
                "/predict", content=valid.content, headers={"Content-Type": "text/csv"}
            )
            self.assertEqual(response.status_code, 200)
            invalid = client.get("/demo/examples/missing-target")
            response = client.post(
                "/predict", content=invalid.content, headers={"Content-Type": "text/csv"}
            )
            self.assertEqual(response.status_code, 422)
            self.assertNotIn("predictions", response.json())

    def test_default_configuration_remains_explicit_and_missing_models_fail(self):
        config = {"run_dir": "results/ci", "demo_dir": "data/demo"}
        with patch("presentation.source.serve_demo.CONFIG", config):
            with TestClient(presentation_app(project_root=self.root)) as client:
                self.assertEqual(client.get("/health").status_code, 200)
        with self.assertRaises(FileNotFoundError):
            presentation_app(
                project_root=self.root, run_dir="results/missing", demo_dir="data/demo"
            )

    def test_overrides_must_include_matching_examples(self):
        with self.assertRaisesRegex(ValueError, "both"):
            presentation_app(project_root=self.root, run_dir="results/ci")
        with self.assertRaisesRegex(ValueError, "both"):
            presentation_app(project_root=self.root, demo_dir="data/demo")
        manifest_path = self.root / "data/demo/manifest.json"
        manifest = json.loads(manifest_path.read_text("utf-8"))
        mismatched = self.root / "data/other-demo"
        mismatched.mkdir()
        (mismatched / "manifest.json").write_text(
            json.dumps({**manifest, "model_version": "wrong"}), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "different run"):
            presentation_app(
                project_root=self.root, run_dir="results/ci", demo_dir="data/other-demo"
            )

    def test_changed_example_is_rejected_before_serving(self):
        manifest = json.loads((self.root / "data/demo/manifest.json").read_text("utf-8"))
        changed = self.root / "data/changed-demo"
        changed.mkdir()
        manifest["examples"][0]["sha256"] = "0" * 64
        (changed / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Artifact differs"):
            presentation_app(
                project_root=self.root, run_dir="results/ci", demo_dir="data/changed-demo"
            )


class PresentationEvidenceTests(unittest.TestCase):
    def test_reference_accepts_checkout_line_endings_but_not_changed_code_or_hash(self):
        text = b"def score(x):\n    return x + 1\n"
        for saved, current in (
            (text, text.replace(b"\n", b"\r\n")),
            (text.replace(b"\n", b"\r\n"), text),
        ):
            record = {
                "path": "source.py",
                "raw": saved.decode(),
                "sha256": hashlib.sha256(saved).hexdigest(),
            }
            check_reference(current, record)
            with self.assertRaises(AssertionError):
                check_reference(current.replace(b"+ 1", b"+ 2"), record)
            with self.assertRaises(AssertionError):
                check_reference(current, {**record, "sha256": "0" * 64})

    def test_response_tolerates_rounding_but_rejects_changed_flags_models_or_scores(self):
        expected = {
            "predictions": [
                {
                    "rejection_score": 0.3,
                    "threshold": 0.8,
                    "rejection_flag": False,
                    "model_version": "saved-model",
                }
            ]
        }
        actual = copy.deepcopy(expected)
        actual["predictions"][0]["rejection_score"] += 1e-16
        check_response(actual, expected)
        for key, value in (
            ("rejection_score", 0.31),
            ("rejection_score", float("nan")),
            ("threshold", 0.81),
            ("rejection_flag", True),
            ("model_version", "another"),
        ):
            actual = copy.deepcopy(expected)
            actual["predictions"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(AssertionError):
                check_response(actual, expected)
