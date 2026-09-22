"""Consequential checks for discovery-only model and threshold selection."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from experiments.rejection_stability.run import (
    DISCOVERY,
    ROOT,
    SEEDS,
    VALIDATION,
    configuration,
    discovery_data,
    fit_and_screen,
    freeze_and_assess,
    run,
    screen_result,
    select_candidate,
    split_discovery,
    validate_parts,
)
from kidney_biopsy import map_diagnoses, predict_scores

DIAGNOSES = [
    "No Rejection",
    "Antibody-mediated Rejection",
    "T cell-mediated Rejection",
    "Mixed Rejection",
]


def synthetic_metadata():
    return pd.DataFrame(
        {
            "cohort": [DISCOVERY] * 1050,
            "histology_diagnosis": [DIAGNOSES[i % 4] for i in range(1050)],
        },
        index=[f"sample_{i}" for i in range(1050)],
    )


class DiscoveryIsolationTests(unittest.TestCase):
    def setUp(self):
        self.metadata = synthetic_metadata()

    def test_all_repetitions_are_disjoint_reproducible_discovery_partitions(self):
        assignments = []
        for seed in SEEDS:
            parts = split_discovery(self.metadata, seed)
            repeated = split_discovery(self.metadata, seed)
            for part in parts:
                np.testing.assert_array_equal(parts[part], repeated[part])
                self.assertEqual(
                    set(self.metadata.loc[parts[part], "histology_diagnosis"]), set(DIAGNOSES)
                )
            self.assertEqual(
                [len(parts[name]) for name in ("fit", "screen", "assessment")], [630, 210, 210]
            )
            self.assertEqual(len(set().union(*map(set, parts.values()))), 1050)
            assignments.append(tuple(parts["assessment"]))
        self.assertEqual(len(set(assignments)), 20)

    def test_overlap_missing_specimen_or_validation_membership_fails(self):
        parts = split_discovery(self.metadata, SEEDS[0])
        overlap = {part: rows.copy() for part, rows in parts.items()}
        overlap["assessment"][0] = overlap["fit"][0]
        with self.assertRaisesRegex(ValueError, "disjoint"):
            validate_parts(overlap, self.metadata)
        missing = {**parts, "assessment": parts["assessment"][:-1]}
        with self.assertRaisesRegex(ValueError, "cover discovery"):
            validate_parts(missing, self.metadata)
        changed = self.metadata.copy()
        changed.iloc[0, 0] = VALIDATION
        with self.assertRaisesRegex(ValueError, "Only unique discovery"):
            validate_parts(parts, changed)
        with self.assertRaisesRegex(ValueError, "exactly the 1,050 discovery"):
            split_discovery(changed, SEEDS[0])

    def test_author_validation_is_removed_before_normalization(self):
        validation = pd.DataFrame(
            {
                "cohort": [VALIDATION] * 345,
                "histology_diagnosis": ["unused by this follow-up"] * 345,
            },
            index=[f"validation_{i}" for i in range(345)],
        )
        metadata = pd.concat([self.metadata, validation])
        counts = pd.DataFrame({"raw": np.arange(1395)}, index=metadata.index)
        normalized = pd.DataFrame(
            np.repeat(np.arange(1050)[:, None], 758, axis=1),
            index=self.metadata.index,
            columns=[f"feature_{i}" for i in range(758)],
        )
        with mock.patch(
            "experiments.rejection_stability.run.normalize_counts", return_value=normalized
        ) as normalize:
            discovery, features, labels = discovery_data(metadata, counts)
        self.assertEqual(set(normalize.call_args.args[0].index), set(self.metadata.index))
        self.assertEqual(set(discovery.index), set(self.metadata.index))
        self.assertEqual(set(features.index), set(labels.index))
        self.assertTrue(set(features.index).isdisjoint(validation.index))

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".uv-cache") as temporary:
            output = Path(temporary)
            marker = output / "preserved.txt"
            marker.write_text("preserve this")
            with self.assertRaisesRegex(ValueError, "already exist"):
                run(output, ROOT / "data/processed/stability/unused_test")
            self.assertEqual(marker.read_text(), "preserve this")


class SelectionTests(unittest.TestCase):
    def test_threshold_keeps_ties_and_highest_eligible_score(self):
        labels = np.array([1] * 10 + [0] * 3)
        scores = np.array([0.1, 0.2, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 0.05, 0.15, 0.95])
        result = screen_result(labels, scores)
        self.assertEqual(result["threshold"], 0.2)
        self.assertEqual(result["fn"], 1)
        self.assertEqual(result["fp"], 1)
        self.assertLess(np.mean(scores[labels == 1] >= 0.4), 0.9)

    def test_invalid_screen_labels_scores_or_missing_class_fail(self):
        for labels, scores in [
            ([0, 0], [0.1, 0.2]),
            ([0, 2], [0.1, 0.2]),
            ([0, 1], [0.2]),
            ([0, 1], [0.2, np.nan]),
            ([0, 1], [0.2, 2]),
        ]:
            with (
                self.subTest(labels=labels, scores=scores),
                self.assertRaisesRegex(ValueError, "Screening needs"),
            ):
                screen_result(labels, scores)

    def test_specificity_then_auc_then_simplicity_determine_selection(self):
        logistic = {
            "family": "logistic",
            "complexity": 0.1,
            "specificity": 0.9,
            "roc_auc": 0.95,
            "sensitivity": 0.91,
        }
        catboost = {**logistic, "family": "catboost", "complexity": 4}
        self.assertIs(select_candidate([catboost, logistic]), logistic)
        better_auc = {**catboost, "roc_auc": 0.96}
        self.assertIs(select_candidate([logistic, better_auc]), better_auc)
        better_specificity = {**logistic, "specificity": 0.95, "roc_auc": 0.94}
        self.assertIs(select_candidate([better_auc, better_specificity]), better_specificity)
        stronger_regularization = {**logistic, "complexity": 0.01}
        self.assertIs(
            select_candidate([logistic, stronger_regularization]), stronger_regularization
        )
        deeper = {**catboost, "complexity": 6}
        self.assertIs(select_candidate([deeper, catboost]), catboost)
        with self.assertRaisesRegex(ValueError, "eligible screening"):
            select_candidate([{**logistic, "sensitivity": 0.89}])

    def test_fit_scaler_uses_only_fit_rows_and_frozen_choice_precedes_assessment(self):
        metadata = synthetic_metadata()
        parts = split_discovery(metadata, SEEDS[0])
        labels = map_diagnoses(metadata.histology_diagnosis)
        rng = np.random.default_rng(4)
        features = pd.DataFrame(
            rng.normal(size=(1050, 3)), index=metadata.index, columns=["IFNG", "A", "B"]
        )
        # Extreme assessment values would noticeably alter an incorrectly fitted scaler.
        features.loc[parts["assessment"]] += 100
        config = configuration()
        config["models"] = {
            "logistic_C0.1": {"family": "logistic", "C": 0.1},
            "catboost_depth4": {"family": "catboost", "depth": 4},
        }
        candidates = {
            "logistic_C0.1": make_pipeline(StandardScaler(), LogisticRegression(C=0.1)),
            "catboost_depth4": CatBoostClassifier(
                iterations=3, depth=4, verbose=False, allow_writing_files=False, thread_count=1
            ),
        }
        with tempfile.TemporaryDirectory(dir=ROOT / ".uv-cache") as temporary:
            destination = Path(temporary)
            with mock.patch(
                "experiments.rejection_stability.run.make_candidates", return_value=candidates
            ):
                models, screen = fit_and_screen(features, labels, parts, config, destination)
            np.testing.assert_allclose(
                models["logistic_C0.1"].named_steps["standardscaler"].mean_,
                features.loc[parts["fit"]].mean(),
            )
            self.assertTrue(all(row["reload_max_abs_difference"] <= 1e-12 for row in screen))
            expected_family = select_candidate(screen)["family"]

            def checked_assessment(model, values):
                frozen = json.loads((destination / "frozen.json").read_text())
                self.assertEqual(frozen["selected_family"], expected_family)
                self.assertEqual(set(values.index), set(parts["assessment"]))
                return predict_scores(model, values)

            with mock.patch(
                "experiments.rejection_stability.run.predict_scores", side_effect=checked_assessment
            ):
                assessment, selected = freeze_and_assess(
                    models, screen, features, labels, parts, destination, "synthetic"
                )
            self.assertEqual(selected["selected_family"], expected_family)
            self.assertEqual(sum(row["selected"] for row in assessment), 1)
            for row in assessment:
                original = next(item for item in screen if item["model"] == row["model"])
                self.assertEqual(row["threshold"], original["threshold"])


if __name__ == "__main__":
    unittest.main()
