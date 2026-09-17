"""Consequential checks for four-class scores, component decisions and data joins."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from experiments.rejection_subtypes.run import (
    DIAGNOSES,
    ROOT,
    component_diagnoses,
    diagnosis_codes,
    fresh_destinations,
    marginal_scores,
    ordered_class_scores,
    subtype_metrics,
    threshold,
    validate_split,
)


class SubtypeScoreTests(unittest.TestCase):
    def setUp(self):
        self.values = pd.DataFrame({"IFNG": [1.0, 2.0]}, index=["a", "b"])

    def test_class_order_is_matched_by_label_before_summing(self):
        model = mock.Mock(classes_=np.array([3, 1, 0, 2]))
        model.predict_proba.return_value = [[0.4, 0.2, 0.1, 0.3], [0.1, 0.2, 0.6, 0.1]]
        score = ordered_class_scores(model, self.values)
        np.testing.assert_allclose(score, [[0.1, 0.2, 0.3, 0.4], [0.6, 0.2, 0.1, 0.1]])
        sums = marginal_scores(score)
        np.testing.assert_allclose(sums["any_rejection"], [0.9, 0.4])
        np.testing.assert_allclose(sums["antibody_mediated_component"], [0.6, 0.3])
        np.testing.assert_allclose(sums["t_cell_mediated_component"], [0.7, 0.2])

    def test_missing_duplicate_or_unrecognized_model_classes_fail(self):
        for labels in [[0, 1, 2], [0, 1, 2, 2], [0, 1, 2, 4], ["0", "1", "2", "3"]]:
            with (
                self.subTest(labels=labels),
                self.assertRaisesRegex(ValueError, "each recorded diagnosis"),
            ):
                ordered_class_scores(mock.Mock(classes_=np.array(labels)), self.values)

    def test_nonfinite_out_of_range_wrong_shape_and_unnormalized_scores_fail(self):
        invalid_scores = [
            [[0.1, 0.2, 0.3, np.nan], [0.25] * 4],
            [[0.1, 0.2, 0.3, np.inf], [0.25] * 4],
            [[-0.1, 0.2, 0.3, 0.6], [0.25] * 4],
            [[1.1, 0, 0, 0], [0.25] * 4],
            [[0.1, 0.2, 0.3, 0.3], [0.25] * 4],
            [[0.25] * 4],
        ]
        for scores in invalid_scores:
            model = mock.Mock(classes_=np.arange(4))
            model.predict_proba.return_value = scores
            with self.subTest(scores=scores), self.assertRaisesRegex(ValueError, "Class scores"):
                ordered_class_scores(model, self.values)

    def test_unknown_or_missing_diagnosis_fails(self):
        for value in ["unknown", None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                diagnosis_codes(pd.Series([DIAGNOSES[0], value]))

    def test_both_component_flags_recognize_mixed_without_binary_gate(self):
        result = component_diagnoses([0.1, 0.5, 0.1, 0.5], [0.1, 0.1, 0.6, 0.6], 0.5, 0.6)
        np.testing.assert_array_equal(result, [0, 1, 2, 3])
        # A specimen exactly at both thresholds is mixed, even if another model would not flag it.
        self.assertEqual(result[-1], 3)

    def test_mismatched_component_rows_or_invalid_thresholds_fail(self):
        for args in [
            ([0.2], [0.3, 0.4], 0.5, 0.5),
            ([0.2], [0.3], np.nan, 0.5),
            ([np.inf], [0.3], 0.5, 0.5),
            ([0.2], [0.3], 0.5, 2),
        ]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                component_diagnoses(*args)

    def test_threshold_includes_ties_and_keeps_at_least_ninety_percent(self):
        y = np.array([1] * 10 + [0] * 3)
        scores = np.array([0.1, 0.2, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 0.05, 0.15, 0.95])
        cutoff = threshold(y, scores)
        self.assertEqual(cutoff, 0.2)
        self.assertEqual(np.mean(scores[y == 1] >= cutoff), 0.9)
        self.assertLess(np.mean(scores[y == 1] >= 0.4), 0.9)

    def test_threshold_rejects_missing_class_bad_labels_and_bad_scores(self):
        invalid = [
            ([1, 1], [0.2, 0.3]),
            ([0, 2], [0.2, 0.3]),
            ([0, 1], [0.2, np.nan]),
            ([0, 1], [0.2, 1.1]),
            ([0, 1], [0.2]),
            ([], []),
        ]
        for y, scores in invalid:
            with self.subTest(y=y, scores=scores), self.assertRaises(ValueError):
                threshold(y, scores)

    def test_no_predicted_mixed_has_undefined_precision_and_zero_sensitivity(self):
        summary, classes, matrix = subtype_metrics([0, 1, 2, 3, 3], np.array([0, 1, 2, 1, 2]))
        mixed = classes[3]
        self.assertEqual(mixed["actual_n"], 2)
        self.assertEqual(mixed["sensitivity"], 0)
        self.assertIsNone(mixed["precision"])
        self.assertIsNone(mixed["precision_lower"])
        self.assertEqual(matrix.shape, (4, 4))
        self.assertEqual(summary["incorrect"], 2)


class SubtypeSplitTests(unittest.TestCase):
    def setUp(self):
        index = [f"specimen{i}" for i in range(1395)]
        self.metadata = pd.DataFrame(
            {
                "histology_diagnosis": [DIAGNOSES[i % 4] for i in range(1395)],
                "cohort": ["Discovery cohort sample"] * 1050 + ["Validation cohort sample"] * 345,
            },
            index=index,
        )
        train, screen = train_test_split(
            np.array(index[:1050]),
            test_size=0.25,
            stratify=self.metadata.histology_diagnosis.iloc[:1050],
            random_state=20260915,
        )
        self.split = pd.DataFrame(
            {"histology": self.metadata.histology_diagnosis, "split": "author_validation"},
            index=index,
        )
        self.split.loc[train, "split"] = "train"
        self.split.loc[screen, "split"] = "discovery_screen"

    def test_split_matches_specimen_names_and_preserves_the_saved_assignment(self):
        result = validate_split(self.split.iloc[::-1], self.metadata)
        pd.testing.assert_frame_equal(result, self.split)

    def test_missing_duplicate_or_different_rows_fail(self):
        for frame in [
            self.split.iloc[:-1],
            pd.concat([self.split, self.split.iloc[:1]]),
            self.split.rename(index={"specimen0": "other"}),
        ]:
            with (
                self.subTest(n=len(frame)),
                self.assertRaisesRegex(ValueError, "same unique specimens"),
            ):
                validate_split(frame, self.metadata)

    def test_changed_diagnosis_or_assignment_fails(self):
        bad = self.split.copy()
        bad.iloc[0, 0] = DIAGNOSES[1]
        with self.assertRaisesRegex(ValueError, "diagnoses disagree"):
            validate_split(bad, self.metadata)
        bad = self.split.copy()
        bad.iloc[0, 1] = "author_validation"
        with self.assertRaisesRegex(ValueError, "fixed diagnosis-stratified"):
            validate_split(bad, self.metadata)

    def test_completed_run_is_preserved(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".uv-cache") as temporary:
            directory = Path(temporary)
            marker = directory / "frozen.json"
            marker.write_text("already complete")
            with self.assertRaisesRegex(ValueError, "already exists"):
                fresh_destinations(
                    directory,
                    ROOT / "data/processed/models/new",
                    ROOT / "data/processed/analysis/new",
                    ROOT / "results/reproduction/baseline",
                )
            self.assertEqual(marker.read_text(), "already complete")

    def test_empty_destinations_are_rejected_before_training(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".uv-cache") as temporary:
            root = Path(temporary)
            outputs = [
                root / "results/new",
                root / "data/processed/models/new",
                root / "data/processed/analysis/new",
            ]
            for destination in outputs:
                destination.mkdir(parents=True)
                with (
                    self.subTest(destination=destination),
                    mock.patch("experiments.rejection_subtypes.run.ROOT", root),
                ):
                    with self.assertRaisesRegex(ValueError, "already exists"):
                        fresh_destinations(*outputs, root / "results/benchmark")
                destination.rmdir()


if __name__ == "__main__":
    unittest.main()
