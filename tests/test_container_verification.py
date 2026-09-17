"""Deployment checks must catch a changed model or missing presentation evidence."""

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

from kidney_biopsy.api import create_app
from scripts.prepare_ci_fixture import prepare_fixture
from scripts.prepare_container import prepare_bundle
from scripts.verify_container import check_service


class ContainerVerificationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        source = Path(temporary.name) / "fixture"
        prepare_fixture(source)
        self.bundle = prepare_bundle(source, "results/ci", "data/demo", "container")
        self.bundle_root = source / "container"
        self.app = create_app(project_root=self.bundle_root, run_dir="results/ci")
        self.client = self.enterContext(TestClient(self.app))

    def verify(self):
        return check_service(self.client, self.bundle_root, self.bundle)

    def test_prepared_service_passes_valid_and_invalid_example_checks(self):
        result = self.verify()
        self.assertEqual(result["valid_specimens"], 1)
        self.assertEqual(result["invalid_examples_rejected"], 1)
        self.assertLessEqual(result["maximum_score_difference"], 1e-12)

    def test_missing_or_changed_displayed_evaluation_fails(self):
        expected = self.app.state.evaluation
        for evaluation in (
            None,
            {**expected, "missed_rejection": expected["missed_rejection"] + 1},
        ):
            with self.subTest(evaluation=evaluation):
                self.app.state.evaluation = evaluation
                with self.assertRaisesRegex(ValueError, "evaluation counts"):
                    self.verify()

    def test_different_model_version_or_threshold_fails(self):
        expected = self.app.state.predictor
        for change in ({"model_version": "another-model"}, {"threshold": 0.9}):
            with self.subTest(change=change):
                self.app.state.predictor = replace(expected, **change)
                with self.assertRaisesRegex(ValueError, "model or schema"):
                    self.verify()

    def test_changed_scores_fail_even_when_version_metadata_agrees(self):
        # Change the live model's scores while leaving its declared version intact.
        self.app.state.predictor.model.set_scale_and_bias(1.0, 10.0)
        with self.assertRaisesRegex(AssertionError, "rejection_score"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
