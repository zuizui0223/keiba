"""Synthetic-only tests of safe Dryad archive inspection."""
from __future__ import annotations
import io
from pathlib import Path
import sys
import unittest
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ecology_dryad_kin_source_preflight import archive_info


class DryadPreflightTests(unittest.TestCase):
    def test_structure_only_and_no_source_rows(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as z:
            z.writestr("work/fake-races.csv", "horse_id,horse_time,sire_id\nPERSONAL_ID_123,9,FAKE_SIRE\n")
        result = archive_info(stream.getvalue())
        self.assertEqual(result["status"], "ARCHIVE_STRUCTURE_OBSERVED_ONLY")
        self.assertEqual(result["member_count"], 1)
        self.assertIn("horse_id", result["member_schema"][0]["header_if_clearly_textual"])
        self.assertNotIn("PERSONAL_ID_123", str(result))
        self.assertNotIn("FAKE_SIRE", str(result))

    def test_not_a_zip(self):
        self.assertEqual(archive_info(b"not a zip")["status"], "HOLD_INVALID_ZIP")


if __name__ == "__main__":
    unittest.main()
