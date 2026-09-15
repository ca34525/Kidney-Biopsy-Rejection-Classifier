"""Consequential input, preprocessing, serialization, and CLI contract checks."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import joblib
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from sklearn.linear_model import LogisticRegression

from kidney_biopsy import (
    AssaySchema, HOUSEKEEPING_TARGETS, Predictor, load_predictor, map_diagnoses,
    normalize_counts, predict_scores, read_counts_csv,
)
from kidney_biopsy.cli import main as predict_main
from kidney_biopsy.prediction import sha256


def raw_counts():
    values = {"IFNG": [0., 10., 50., 100.], "CXCL9": [1., 8., 80., 90.]}
    values.update({name: [1., 2., 3., 4.] for name in HOUSEKEEPING_TARGETS})
    return pd.DataFrame(values, index=["001", "002", "003", "004"])


class PreprocessingTests(unittest.TestCase):
    def setUp(self):
        self.raw = raw_counts()
        self.schema = AssaySchema(("IFNG", "CXCL9"))

    def test_training_and_reordered_csv_have_identical_preprocessing(self):
        training = normalize_counts(self.raw)
        csv_text = self.raw.iloc[:, ::-1].to_csv(index_label="specimen")
        parsed = read_counts_csv(io.StringIO(csv_text), self.schema)
        prediction = normalize_counts(parsed, self.schema)
        prediction.index.name = None
        assert_frame_equal(training, prediction, check_exact=True)
        self.assertEqual(list(parsed.index), ["001", "002", "003", "004"])
        # Independent arithmetic example, including a zero target count.
        self.assertEqual(training.loc["001", "IFNG"], -1.)
        self.assertEqual(training.loc["001", "CXCL9"], 0.)

    def test_specimen_normalization_does_not_depend_on_batch(self):
        assert_frame_equal(normalize_counts(self.raw.iloc[[2]], self.schema),
                           normalize_counts(self.raw, self.schema).iloc[[2]], check_exact=True)

    def test_missing_housekeeping_or_predictor_targets_fail(self):
        for target in ("IFNG", HOUSEKEEPING_TARGETS[0]):
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, "Missing required"):
                normalize_counts(self.raw.drop(columns=target), self.schema)

    def test_duplicate_targets_cannot_be_renamed_or_silently_dropped(self):
        duplicate = pd.concat([self.raw, self.raw[["IFNG"]]], axis=1)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            normalize_counts(duplicate, self.schema)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            read_counts_csv(io.StringIO(duplicate.to_csv(index_label="specimen")), self.schema)

    def test_extra_metadata_or_assay_targets_fail(self):
        for extra in ("diagnosis", "unexpected_assay_target"):
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError, "Unexpected"):
                normalize_counts(self.raw.assign(**{extra: 1}), self.schema)

    def test_nonnumeric_negative_and_nonfinite_counts_fail_entire_batch(self):
        for value in ("bad", "", -1, np.nan, np.inf, -np.inf):
            data = self.raw.astype(object)
            data.loc["002", "IFNG"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_counts(data, self.schema)

    def test_empty_missing_or_duplicate_specimens_fail(self):
        cases = [self.raw.iloc[:0], self.raw.set_axis(["x", "x", "y", "z"]),
                 self.raw.set_axis(["", "x", "y", "z"]), self.raw.set_axis([None, "x", "y", "z"])]
        for frame in cases:
            with self.subTest(index=list(frame.index)), self.assertRaises(ValueError):
                normalize_counts(frame, self.schema)

    def test_empty_csv_malformed_rows_and_batch_limit_fail(self):
        for text in ("", "specimen,IFNG\n", "specimen,IFNG\na,1,2\n", "specimen,IFNG\n\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                read_counts_csv(io.StringIO(text), self.schema)
        with self.assertRaisesRegex(ValueError, "batch limit"):
            read_counts_csv(io.StringIO(self.raw.to_csv(index_label="specimen")), self.schema, max_specimens=3)

    def test_unknown_and_missing_diagnoses_fail(self):
        labels = pd.Series(["No Rejection", "Antibody-mediated Rejection", "T cell-mediated Rejection", "Mixed Rejection"])
        self.assertEqual(map_diagnoses(labels).tolist(), [0, 1, 1, 1])
        for label in ("Borderline", None, ""):
            with self.subTest(label=label), self.assertRaises(ValueError):
                map_diagnoses(pd.Series(["No Rejection", label]))

    def test_schema_version_housekeepers_and_duplicate_features_fail(self):
        invalid = [dict(features=("IFNG", "IFNG")), dict(features=("IFNG",), schema_version="v99"),
                   dict(features=("IFNG",), preprocessing_version="wrong"),
                   dict(features=("IFNG",), housekeeping_targets=HOUSEKEEPING_TARGETS[:-1])]
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                AssaySchema(**kwargs)


class PredictionTests(unittest.TestCase):
    def setUp(self):
        self.raw = raw_counts()
        self.schema = AssaySchema(("IFNG", "CXCL9"))
        self.x = normalize_counts(self.raw, self.schema)
        self.model = LogisticRegression().fit(self.x, [0, 0, 1, 1])
        self.predictor = Predictor(self.model, self.schema, .5, "test-v1")
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "results/test").mkdir(parents=True)
        (self.root / "data/models").mkdir(parents=True)
        self.model_path = self.root / "data/models/any_rejection_selected_model.joblib"
        self.frozen_path = self.root / "results/test/any_rejection_frozen.json"
        joblib.dump(self.model, self.model_path)
        self.frozen = {"features": list(self.schema.features), "schema": self.schema.to_dict(),
                       "threshold": .5, "target": "any_rejection", "selected_model": "logistic", "model_version": "test-v1"}
        self.write_manifest()

    def tearDown(self):
        self.temp.cleanup()

    def write_manifest(self):
        self.frozen_path.write_text(json.dumps(self.frozen), encoding="utf-8")
        artifacts = [{"file": path.relative_to(self.root).as_posix(), "bytes": path.stat().st_size,
                      "sha256": sha256(path)} for path in (self.model_path, self.frozen_path)]
        (self.root / "results/test/run_manifest.json").write_text(
            json.dumps({"model_dir": "data/models", "artifacts": artifacts}), encoding="utf-8")

    def test_save_load_and_reordered_raw_columns_preserve_scores_and_flags(self):
        reloaded = load_predictor(self.root, "results/test")
        direct = self.predictor.predict(self.raw)
        result = reloaded.predict(self.raw.iloc[:, ::-1])
        assert_frame_equal(direct, result, atol=1e-12, rtol=0)
        np.testing.assert_allclose(result.rejection_score, predict_scores(self.model, self.x), rtol=0, atol=1e-12)
        self.assertEqual(result.rejection_flag.tolist(), (result.rejection_score >= .5).tolist())

    def test_hash_mismatch_is_detected_before_model_deserialization(self):
        with self.model_path.open("ab") as stream:
            stream.write(b"changed")
        with patch("kidney_biopsy.prediction.joblib.load") as deserializer:
            with self.assertRaisesRegex(ValueError, "manifest"):
                load_predictor(self.root, "results/test")
            deserializer.assert_not_called()

    def test_frozen_schema_order_mismatch_fails_even_with_matching_hashes(self):
        self.frozen["schema"]["features"].reverse()
        self.frozen["features"].reverse()
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "Model feature names or order"):
            load_predictor(self.root, "results/test")

    def test_schema_version_or_threshold_mismatch_fails(self):
        for field, value in (("threshold", float("nan")), ("preprocessing_version", "bad-v2")):
            original = self.frozen.copy()
            self.frozen[field] = value
            self.write_manifest()
            with self.subTest(field=field), self.assertRaises(ValueError):
                load_predictor(self.root, "results/test")
            self.frozen = original

    def test_mismatched_model_directory_and_traversal_fail(self):
        with self.assertRaisesRegex(ValueError, "directory"):
            load_predictor(self.root, "results/test", "data/other")
        with self.assertRaisesRegex(ValueError, "relative"):
            load_predictor(self.root, "../elsewhere")

    def test_unexpected_model_classes_or_invalid_scores_fail(self):
        with patch.object(self.model, "classes_", np.array([1, 0])):
            with self.assertRaisesRegex(ValueError, "classes"):
                predict_scores(self.model, self.x)
        for values in (np.full((4, 2), np.nan), np.ones((4, 1)), np.full((4, 2), .9), np.full((4, 2), -1.)):
            with patch.object(self.model, "predict_proba", return_value=values):
                with self.subTest(shape=values.shape), self.assertRaisesRegex(ValueError, "invalid binary scores"):
                    predict_scores(self.model, self.x)

    def test_cli_uses_same_predictor_and_preserves_existing_output(self):
        self.raw.to_csv(self.root / "counts.csv", index_label="specimen")
        args = ["--project-root", str(self.root), "--counts-csv", "counts.csv",
                "--results-dir", "results/test", "--output", "inference.csv"]
        with redirect_stdout(io.StringIO()):
            predict_main(args)
        result = pd.read_csv(self.root / "inference.csv", dtype={"specimen": str})
        expected = self.predictor.predict(self.raw)
        assert_frame_equal(result, expected, atol=1e-12, rtol=0)
        original_hash = sha256(self.root / "inference.csv")
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            predict_main(args)
        self.assertEqual(sha256(self.root / "inference.csv"), original_hash)

    def test_bad_batch_does_not_create_output(self):
        self.raw.drop(columns="IFNG").to_csv(self.root / "invalid.csv", index_label="specimen")
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            predict_main(["--project-root", str(self.root), "--counts-csv", "invalid.csv",
                          "--results-dir", "results/test", "--output", "invalid_result.csv"])
        self.assertFalse((self.root / "invalid_result.csv").exists())


if __name__ == "__main__":
    unittest.main()
