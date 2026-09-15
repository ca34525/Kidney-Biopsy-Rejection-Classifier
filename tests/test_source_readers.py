"""Check malformed source files cannot silently change the training matrix."""
import gzip
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

import pandas as pd

from kidney_biopsy import HOUSEKEEPING_TARGETS, read_geo_matrix, read_rcc_archive


class GeoMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "matrix.txt.gz"
        self.metadata = [
            '!Sample_geo_accession\t"a"\t"b"',
            '!Sample_title\t"Biopsy A"\t"Biopsy B"',
            '!Sample_characteristics_ch1\t"cohort: Discovery cohort sample"\t"cohort: Validation cohort sample"',
            '!Sample_characteristics_ch1\t"histology diganosis of rejection: No Rejection"\t"histology diganosis of rejection: Mixed Rejection"',
        ]

    def tearDown(self):
        self.temp.cleanup()

    def write_matrix(self, metadata):
        text = "\n".join(metadata) + '\n!series_matrix_table_begin\n"ID_REF"\t"a"\t"b"\n"IFNG"\t1\t2\n!series_matrix_table_end\n'
        self.path.write_bytes(gzip.compress(text.encode()))

    def test_metadata_retains_source_labels_and_matches_expression_specimens(self):
        self.write_matrix(self.metadata)
        expression, metadata = read_geo_matrix(self.path)
        self.assertEqual(list(expression.index), list(metadata.index))
        self.assertEqual(metadata.histology_diagnosis.tolist(), ["No Rejection", "Mixed Rejection"])
        self.assertEqual(metadata.cohort.tolist(), ["Discovery cohort sample", "Validation cohort sample"])

    def test_duplicate_metadata_cannot_silently_replace_labels_or_cohorts(self):
        for duplicate in (
            '!Sample_characteristics_ch1\t"cohort: Validation cohort sample"\t"cohort: Discovery cohort sample"',
            '!Sample_characteristics_ch1\t"histology diganosis of rejection: Mixed Rejection"\t"histology diganosis of rejection: No Rejection"',
            '!Sample_title\t"Changed A"\t"Changed B"',
        ):
            self.write_matrix([*self.metadata, duplicate])
            with self.subTest(row=duplicate), self.assertRaisesRegex(ValueError, "Duplicate GEO metadata"):
                read_geo_matrix(self.path)

    def test_missing_or_duplicate_accession_rows_fail_clearly(self):
        for metadata in (self.metadata[1:], [*self.metadata, self.metadata[0]]):
            self.write_matrix(metadata)
            with self.subTest(rows=len(metadata)), self.assertRaisesRegex(ValueError, "exactly one"):
                read_geo_matrix(self.path)


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
