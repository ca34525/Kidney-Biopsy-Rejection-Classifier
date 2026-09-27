"""Keep a Windows-recorded guide buildable without accepting changed calculations."""

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

BUILDER = Path(__file__).resolve().parents[1] / "scripts/build_code_guide.py"
SPEC = importlib.util.spec_from_file_location("code_guide_builder", BUILDER)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class CalculationSourceTests(unittest.TestCase):
    def test_checkout_line_endings_do_not_require_recalculating_the_example(self):
        lf = b"def normalize(x):\n    return x - 1\n"
        crlf = lf.replace(b"\n", b"\r\n")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "calculation.py"
            for recorded, checked_out in ((crlf, lf), (lf, crlf), (lf, lf)):
                with self.subTest(recorded=recorded, checked_out=checked_out):
                    source.write_bytes(checked_out)
                    self.assertTrue(
                        builder.matches_calculation_source(
                            source, hashlib.sha256(recorded).hexdigest()
                        )
                    )

    def test_a_changed_calculation_still_requires_refresh(self):
        recorded = b"def normalize(x):\r\n    return x - 1\r\n"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "calculation.py"
            source.write_bytes(b"def normalize(x):\n    return x - 2\n")
            self.assertFalse(
                builder.matches_calculation_source(source, hashlib.sha256(recorded).hexdigest())
            )
