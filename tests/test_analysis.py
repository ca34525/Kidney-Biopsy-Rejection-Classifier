"""Consequential analysis checks; no public inputs or fitted models needed."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

from scripts.analyze_results import (
    ROOT,
    align_predictions,
    binary_labels,
    main,
    metrics,
    paired_bootstrap,
    project_path,
    reliability,
    wilson,
)
from scripts.review_viral_targets import higher_signal_outcomes


class AnalysisValidationTests(unittest.TestCase):
    def setUp(self):
        self.reference = pd.DataFrame(
            {"histology": ["No Rejection", "Mixed Rejection"]}, index=["a", "b"]
        )
        self.predictions = pd.DataFrame(
            {"y": [0, 1], "probability": [0.2, 0.8], "predicted": ["False", "True"]},
            index=["a", "b"],
        )

    def test_prediction_join_matches_names_not_row_positions(self):
        result = align_predictions(self.predictions.iloc[::-1], self.reference, 0.5)
        np.testing.assert_array_equal(result.probability, [0.2, 0.8])
        np.testing.assert_array_equal(result.predicted, [False, True])

    def test_unequal_and_duplicate_specimen_sets_fail(self):
        bad = [
            self.predictions.iloc[:1],
            self.predictions.rename(index={"b": "c"}),
            pd.concat([self.predictions, self.predictions.iloc[:1]]),
        ]
        for frame in bad:
            with self.subTest(index=frame.index.tolist()), self.assertRaises(ValueError):
                align_predictions(frame, self.reference, 0.5)

    def test_bad_labels_scores_and_frozen_decisions_fail(self):
        for column, value in [
            ("y", 1),
            ("probability", np.nan),
            ("probability", np.inf),
            ("probability", -0.1),
            ("probability", 1.1),
            ("predicted", "maybe"),
            ("predicted", "True"),
        ]:
            bad = self.predictions.copy()
            bad.loc["a", column] = value
            with self.subTest(column=column, value=value), self.assertRaises(ValueError):
                align_predictions(bad, self.reference, 0.5)

    def test_unknown_or_missing_diagnosis_fails(self):
        for value in ["unknown", None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                binary_labels(pd.Series(["No Rejection", value]))

    def test_completed_destination_is_not_overwritten(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".uv-cache") as temporary:
            root = Path(temporary)
            saved = root / "already_done"
            saved.mkdir()
            marker = saved / "preserved.txt"
            marker.write_text("preserve this")
            with (
                mock.patch("scripts.analyze_results.ROOT", root),
                mock.patch("sys.argv", ["analyze_results.py", "--output-dir", "already_done"]),
                mock.patch("scripts.analyze_results.load_run") as load,
            ):
                with self.assertRaisesRegex(ValueError, "already exists"):
                    main()
                load.assert_not_called()
            self.assertEqual(marker.read_text(), "preserve this")

    def test_empty_destination_is_rejected_before_reading_run(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".uv-cache") as temporary:
            root = Path(temporary)
            (root / "empty").mkdir()
            with (
                mock.patch("scripts.analyze_results.ROOT", root),
                mock.patch("sys.argv", ["analyze_results.py", "--output-dir", "empty"]),
                mock.patch("scripts.analyze_results.load_run") as load,
            ):
                with self.assertRaisesRegex(ValueError, "already exists"):
                    main()
                load.assert_not_called()
            self.assertEqual(list((root / "empty").iterdir()), [])

    def test_analysis_paths_reject_absolute_traversal_and_linked_inputs(self):
        for value in [str(ROOT / "data"), "../data", "data/../data"]:
            with self.subTest(path=value), self.assertRaises(ValueError):
                project_path(value)
        with mock.patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaisesRegex(ValueError, "Linked"):
                project_path("data/raw/input.csv")


class ViralReviewTests(unittest.TestCase):
    def test_higher_signal_counts_distinguish_false_flags_and_missed_rejection(self):
        frame = pd.DataFrame(
            {
                "diagnosis": [
                    "No Rejection",
                    "No Rejection",
                    "Mixed Rejection",
                    "Mixed Rejection",
                    "No Rejection",
                ],
                "predicted": pd.Series([False, True, False, True, True], dtype=object),
                "both_BK_signals_above_zero": [True, True, True, True, False],
            }
        )
        self.assertEqual(
            higher_signal_outcomes(frame),
            {
                "n": 4,
                "no_rejection": 2,
                "rejection": 2,
                "negative_results": 2,
                "false_flags": 1,
                "missed_rejection": 1,
            },
        )
        frame["both_BK_signals_above_zero"] = False
        self.assertTrue(all(value == 0 for value in higher_signal_outcomes(frame).values()))


class UncertaintyTests(unittest.TestCase):
    def test_all_positive_constant_has_undefined_npv(self):
        row = metrics(np.array([0, 0, 1, 1]), np.full(4, 0.7), 0.5)
        self.assertTrue(np.isnan(row["npv"]))
        self.assertEqual((row["fn"], row["fp"], row["roc_auc"]), (0, 2, 0.5))

    def test_reliability_keeps_empty_bins_and_includes_one(self):
        rows = reliability(np.array([0, 1, 0, 1]), np.array([0, 0.1, 0.99, 1]), "model")
        self.assertEqual(len(rows), 10)
        self.assertEqual([row["n"] for row in rows], [1, 1, 0, 0, 0, 0, 0, 0, 0, 2])
        self.assertEqual(rows[-1]["observed_fraction"], 0.5)
        self.assertTrue(np.isnan(rows[2]["observed_fraction"]))
        lo, hi = wilson(0, 10)
        self.assertAlmostEqual(lo, 0)
        self.assertGreater(hi, 0.25)

    def test_pairing_preserves_identical_model_differences_and_seed(self):
        y = np.tile([0, 1], 10)
        score = np.linspace(0.02, 0.98, len(y))
        values = {
            "selected": score,
            "comparison": score.copy(),
            "training_prevalence": np.full(len(y), 0.7),
        }
        thresholds = {key: 0.5 for key in values}
        _, intervals, differences = paired_bootstrap(y, values, thresholds, 40, 17)
        _, repeat, repeated_differences = paired_bootstrap(y, values, thresholds, 40, 17)
        pd.testing.assert_frame_equal(intervals, repeat)
        pd.testing.assert_frame_equal(differences, repeated_differences)
        np.testing.assert_array_equal(differences[["estimate", "lower", "upper"]], 0)
        row = intervals.loc[
            (intervals.model == "training_prevalence") & (intervals.metric == "npv")
        ].iloc[0]
        self.assertEqual(row.valid_replicates, 0)
        self.assertTrue(np.isnan(row.lower))


if __name__ == "__main__":
    unittest.main()
