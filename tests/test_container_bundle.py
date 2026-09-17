"""A serving bundle must be complete, unchanged, and tied to one trusted model."""

import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from kidney_biopsy.api import create_app
from kidney_biopsy.prediction import load_predictor, sha256, verify_artifact
from kidney_biopsy.preprocessing import read_counts_csv
from scripts.prepare_ci_fixture import prepare_fixture
from scripts.prepare_container import prepare_bundle


class ContainerBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "fixture"
        prepare_fixture(self.root)
        self.output = self.root / "container"
        self.demo_manifest = self.root / "data/demo/manifest.json"
        self.run_manifest = self.root / "results/ci/run_manifest.json"

    def prepare(self):
        return prepare_bundle(self.root, "results/ci", "data/demo", "container")

    def write_json(self, path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def update_artifact(self, path):
        manifest = json.loads(self.run_manifest.read_text(encoding="utf-8"))
        for artifact in manifest["artifacts"]:
            if artifact["file"] == path.relative_to(self.root).as_posix():
                artifact.update(bytes=path.stat().st_size, sha256=sha256(path))
        self.write_json(self.run_manifest, manifest)

    def test_bundle_serves_same_model_and_examples_without_source_data(self):
        unrelated = self.root / "data/unrelated-training-data.csv"
        unrelated.write_text("must stay outside the image", encoding="utf-8")
        before = {
            path.relative_to(self.root): sha256(path)
            for path in self.root.rglob("*")
            if path.is_file()
        }
        bundle = self.prepare()
        copied = {item["file"] for item in bundle["files"]}
        self.assertNotIn("data/unrelated-training-data.csv", copied)
        self.assertEqual(len(copied), 7)
        self.assertEqual(bundle["model_version"], "synthetic-ci-only")
        for item in bundle["files"]:
            verify_artifact(self.output, item)
        for relative, original_hash in before.items():
            self.assertEqual(sha256(self.root / relative), original_hash)

        counts = read_counts_csv(self.root / "data/demo/valid.csv")
        expected = load_predictor(self.root, "results/ci").predict(counts).iloc[0]
        # The API sees only the copied root, never the source fixture directory.
        with TestClient(create_app(project_root=self.output, run_dir="results/ci")) as client:
            self.assertEqual(client.get("/health").status_code, 200)
            self.assertIsNotNone(client.get("/model").json()["evaluation"])
            response = client.post(
                "/predict",
                content=client.get("/demo/examples/valid").content,
                headers={"Content-Type": "text/csv"},
            )
            self.assertEqual(response.status_code, 200)
            actual = response.json()["predictions"][0]
            self.assertAlmostEqual(actual["rejection_score"], expected.rejection_score, places=12)
            self.assertEqual(actual["rejection_flag"], bool(expected.rejection_flag))
            invalid = client.post(
                "/predict",
                content=client.get("/demo/examples/missing-target").content,
                headers={"Content-Type": "text/csv"},
            )
            self.assertEqual(invalid.status_code, 422)

    def test_existing_bundle_is_preserved(self):
        self.prepare()
        before = sha256(self.output / "bundle.json")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.prepare()
        self.assertEqual(sha256(self.output / "bundle.json"), before)

    def test_tampered_model_metadata_results_or_demo_fail_before_output(self):
        for relative in [
            "data/models/any_rejection_selected_model.joblib",
            "results/ci/any_rejection_frozen.json",
            "results/ci/biopsy_results.json",
            "data/demo/valid.csv",
        ]:
            path = self.root / relative
            original = path.read_bytes()
            path.write_bytes(original + b"changed")
            with self.subTest(file=relative), self.assertRaisesRegex(ValueError, "manifest"):
                self.prepare()
            self.assertFalse(self.output.exists())
            path.write_bytes(original)

    def test_missing_required_artifact_fails_before_output(self):
        (self.root / "data/models/any_rejection_selected_model.joblib").unlink()
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_demo_run_or_model_mismatch_fails(self):
        original = json.loads(self.demo_manifest.read_text(encoding="utf-8"))
        for field in ("run_dir", "model_version"):
            self.write_json(self.demo_manifest, {**original, field: "another-run"})
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(ValueError, "different run or model"),
            ):
                self.prepare()
            self.assertFalse(self.output.exists())

    def test_evaluation_threshold_must_match_even_when_hashes_are_updated(self):
        path = self.root / "results/ci/biopsy_results.json"
        results = json.loads(path.read_text(encoding="utf-8"))
        results["any_rejection"]["author_validation"]["catboost"]["threshold"] = 0.9
        self.write_json(path, results)
        self.update_artifact(path)
        with self.assertRaisesRegex(ValueError, "threshold"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_incompatible_schema_fails_even_when_hashes_are_updated(self):
        path = self.root / "results/ci/any_rejection_frozen.json"
        frozen = json.loads(path.read_text(encoding="utf-8"))
        frozen["schema"]["schema_version"] = "incompatible-v99"
        self.write_json(path, frozen)
        self.update_artifact(path)
        with self.assertRaisesRegex(ValueError, "schema"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_example_validity_labels_are_checked_against_the_frozen_schema(self):
        original = self.demo_manifest.read_text(encoding="utf-8")
        for index in (0, 1):
            manifest = json.loads(original)
            manifest["examples"][index]["valid"] = not manifest["examples"][index]["valid"]
            self.write_json(self.demo_manifest, manifest)
            with self.subTest(example=index), self.assertRaisesRegex(ValueError, "marked"):
                self.prepare()
            self.assertFalse(self.output.exists())

    def test_duplicate_ids_or_copy_paths_fail_before_output(self):
        original = self.demo_manifest.read_text(encoding="utf-8")
        for field in ("id", "file"):
            manifest = json.loads(original)
            duplicate = dict(manifest["examples"][0])
            if field == "file":
                duplicate["id"] = "another-id"
            manifest["examples"].append(duplicate)
            self.write_json(self.demo_manifest, manifest)
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.prepare()
            self.assertFalse(self.output.exists())

    def test_unsafe_paths_and_aliases_fail_before_output(self):
        original = self.demo_manifest.read_text(encoding="utf-8")
        for relative in (
            "../valid.csv",
            "data/demo/./valid.csv",
            "data/demo/../valid.csv",
            "C:/valid.csv",
        ):
            manifest = json.loads(original)
            manifest["examples"][0]["file"] = relative
            self.write_json(self.demo_manifest, manifest)
            with self.subTest(path=relative), self.assertRaises(ValueError):
                self.prepare()
            self.assertFalse(self.output.exists())
        with self.assertRaises(ValueError):
            prepare_bundle(self.root, "results/ci", "data/demo", "../outside")
        self.assertFalse((self.root.parent / "outside").exists())


if __name__ == "__main__":
    unittest.main()
