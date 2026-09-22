"""Error examples must match recorded diagnoses and stay in the screening split."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd

from scripts.prepare_demo import select_error_examples


class DemoExampleTests(unittest.TestCase):
    def setUp(self):
        # Earlier accessions outside screening must not become demo examples.
        specimens = ["validation", "training", "screen-c", "screen-b", "screen-a"]
        self.counts = pd.DataFrame({"IFNG": [90, 80, 70, 20, 60]}, index=specimens)
        self.metadata = pd.DataFrame(
            {"histology_diagnosis": ["No Rejection"] * 3 + ["Mixed Rejection", "No Rejection"]},
            index=specimens,
        )
        self.split = pd.DataFrame(
            {"split": ["technical_validation", "discovery_train"] + ["discovery_screen"] * 3},
            index=specimens,
        )
        self.predictor = Mock(schema=SimpleNamespace(required_targets=("IFNG",)))
        # A different prediction order checks the specimen join as well as selection.
        self.predictor.predict.return_value = pd.DataFrame(
            {
                "specimen": ["screen-c", "screen-b", "screen-a"],
                "rejection_flag": [True, False, True],
            }
        )

    def test_selects_first_actual_errors_by_specimen_within_screening(self):
        selected = select_error_examples(
            self.counts, self.metadata.iloc[::-1], self.split, self.predictor
        )
        self.assertEqual(
            [(ident, diagnosis, specimen) for ident, diagnosis, specimen, _ in selected],
            [
                ("false-positive", "No Rejection", "screen-a"),
                ("false-negative", "Mixed Rejection", "screen-b"),
            ],
        )
        scored = self.predictor.predict.call_args.args[0]
        self.assertEqual(set(scored.index), {"screen-a", "screen-b", "screen-c"})
        for _, _, specimen, frame in selected:
            pd.testing.assert_frame_equal(frame, self.counts.loc[[specimen]])

    def test_refuses_to_invent_an_error_example_when_no_matching_error_exists(self):
        self.predictor.predict.return_value["rejection_flag"] = [False, True, False]
        with self.assertRaisesRegex(ValueError, "No discovery-screen false-positive"):
            select_error_examples(self.counts, self.metadata, self.split, self.predictor)
        self.predictor.predict.return_value["rejection_flag"] = [True, True, True]
        with self.assertRaisesRegex(ValueError, "No discovery-screen false-negative"):
            select_error_examples(self.counts, self.metadata, self.split, self.predictor)

    def test_rejects_unknown_diagnosis_before_labeling_an_error(self):
        self.metadata.loc["screen-b", "histology_diagnosis"] = "Unknown"
        with self.assertRaisesRegex(ValueError, "Unexpected recorded rejection diagnoses"):
            select_error_examples(self.counts, self.metadata, self.split, self.predictor)
        self.predictor.predict.assert_not_called()
