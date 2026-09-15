"""Check malformed source files cannot silently change the training matrix."""
import gzip
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

import pandas as pd

from kidney_biopsy import HOUSEKEEPING_TARGETS, read_rcc_archive


class RawSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "raw.tar"
        self.targets = ["IFNG", *[f"target{i}" for i in range(757)], *HOUSEKEEPING_TARGETS]

    def tearDown(self):
        self.temp.cleanup()

    def write_archive(self, specimens):
        with tarfile.open(self.path, "w") as archive:
            for filename, targets in specimens:
                table = pd.DataFrame({"CodeClass": ["Housekeeping" if name in HOUSEKEEPING_TARGETS else "Endogenous" for name in targets],
                                      "Name": targets, "Count": 10})
                body = "Date,2020-01-01\nCartridgeID,test\nScannerID,scanner\n<Code_Summary>\n"
                body += table.to_csv(index=False) + "</Code_Summary>\n"
                payload = gzip.compress(body.encode())
                member = tarfile.TarInfo(filename)
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))

    def test_source_join_uses_requested_order_and_keeps_batch_metadata_separate(self):
        self.write_archive([("a_counts.gz", self.targets), ("b_counts.gz", self.targets)])
        counts, metadata = read_rcc_archive(self.path, specimen_ids=["b", "a"])
        self.assertEqual(list(counts.index), ["b", "a"])
        self.assertEqual(list(counts.columns), self.targets)
        self.assertEqual(counts.shape, (2, 770))
        self.assertEqual(list(metadata.columns), ["Date", "CartridgeID", "ScannerID"])
        self.assertFalse(set(metadata.columns).intersection(counts.columns))

    def test_duplicate_rcc_targets_are_detected_before_dictionary_conversion(self):
        self.write_archive([("a_counts.gz", self.targets + ["IFNG"])])
        with self.assertRaisesRegex(ValueError, "duplicate targets"):
            read_rcc_archive(self.path)

    def test_different_per_specimen_panels_cannot_be_silently_union_joined(self):
        self.write_archive([("a_counts.gz", self.targets), ("b_counts.gz", self.targets[1:])])
        with self.assertRaisesRegex(ValueError, "present for every assay target"):
            read_rcc_archive(self.path)

    def test_duplicate_specimen_archives_and_incomplete_metadata_joins_fail(self):
        self.write_archive([("a_first.gz", self.targets), ("a_second.gz", self.targets)])
        with self.assertRaisesRegex(ValueError, "duplicate specimen"):
            read_rcc_archive(self.path)
        self.write_archive([("a_counts.gz", self.targets), ("b_counts.gz", self.targets)])
        with self.assertRaisesRegex(ValueError, "match exactly"):
            read_rcc_archive(self.path, specimen_ids=["a"])


if __name__ == "__main__":
    unittest.main()
