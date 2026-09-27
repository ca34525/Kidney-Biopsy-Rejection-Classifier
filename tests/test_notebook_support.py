"""Prevent misleading notebook results from mismatched splits or modified artifacts."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from kidney_biopsy.prediction import sha256
from notebooks import notebook_support as support


class NotebookSplitTests(unittest.TestCase):
    def setUp(self):
        self.metadata = pd.DataFrame(
            {
                "histology_diagnosis": ["No Rejection", "Mixed Rejection", "Mixed Rejection"],
                "cohort": [
                    "Discovery cohort sample",
                    "Discovery cohort sample",
                    "Validation cohort sample",
                ],
            },
            index=["a", "b", "c"],
        )
        self.split = pd.DataFrame(
            {
                "histology": self.metadata.histology_diagnosis,
                "split": ["train", "discovery_screen", "author_validation"],
            }
        )

    def test_shuffled_split_aligns_by_specimen(self):
        actual = support.validate_split(self.split.iloc[::-1], self.metadata)
        pd.testing.assert_frame_equal(actual, self.split)

    def test_wrong_or_duplicate_specimens_fail(self):
        for split in [
            self.split.iloc[:2],
            self.split.rename(index={"c": "other"}),
            pd.concat([self.split, self.split.iloc[:1]]),
        ]:
            with self.subTest(index=split.index.tolist()), self.assertRaises(ValueError):
                support.validate_split(split, self.metadata)

    def test_label_or_cohort_changes_fail(self):
        for column, value in [
            ("histology", "Mixed Rejection"),
            ("split", "author_validation"),
            ("split", "unknown"),
        ]:
            changed = self.split.copy()
            changed.loc["a", column] = value
            with self.subTest(column=column, value=value), self.assertRaises(ValueError):
                support.validate_split(changed, self.metadata)
        changed_metadata = self.metadata.copy()
        changed_metadata.loc["a", "histology_diagnosis"] = "unknown"
        with self.assertRaises(ValueError):
            support.validate_split(self.split, changed_metadata)


class NotebookArtifactTests(unittest.TestCase):
    def test_changed_artifact_is_rejected_and_completed_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest = root / "data/manifest.json"
            manifest.parent.mkdir()
            manifest.write_text("[]", encoding="utf-8")
            run = root / "results/reproduction/example"
            run.mkdir(parents=True)
            artifact = run / "biopsy_split.csv"
            artifact.write_text("original", encoding="utf-8")
            record = {
                "input_manifest_sha256": sha256(manifest),
                "artifacts": [
                    {
                        "file": artifact.relative_to(root).as_posix(),
                        "bytes": artifact.stat().st_size,
                        "sha256": sha256(artifact),
                    }
                ],
            }
            (run / "run_manifest.json").write_text(json.dumps(record), encoding="utf-8")
            env = {
                "KIDNEY_BIOPSY_NOTEBOOK_RUN": "results/reproduction/example",
                "KIDNEY_BIOPSY_NOTEBOOK_OUTPUT": "results/notebooks/example",
            }
            with patch.object(support, "ROOT", root), patch.dict("os.environ", env):
                session = support.NotebookSession("01_example")
                self.assertEqual(session.artifact("biopsy_split.csv"), artifact)
                artifact.write_text("modified", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "differs"):
                    session.artifact("biopsy_split.csv")
                with self.assertRaises(FileExistsError):
                    support.NotebookSession("01_example")


if __name__ == "__main__":
    unittest.main()
